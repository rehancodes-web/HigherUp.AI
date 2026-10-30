
import os
from pathlib import Path
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from hdbcli import dbapi
from skills_agent import discover

# Load the .env located beside main.py
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="HigherUp.AI API")
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-File-Name", "X-Document-Kind"],
)


def get_db_connection():
    required = [
        "HANA_ADDRESS",
        "HANA_PORT",
        "HANA_USER",
        "HANA_PASSWORD",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing .env settings: {', '.join(missing)}"
        )

    return dbapi.connect(
        address=os.environ["HANA_ADDRESS"].strip(),
        port=int(os.environ["HANA_PORT"]),
        user=os.environ["HANA_USER"].strip(),
        password=os.environ["HANA_PASSWORD"],
        encrypt=True,
        sslValidateCertificate=True,
        connectTimeout=30000,
    )


def require_candidate_email(authorization: str | None, expected_email: str) -> None:
    """Verify the Supabase access token and ensure it belongs to this candidate."""
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request as UrlRequest, urlopen

    token = (authorization or "").removeprefix("Bearer ").strip()
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    if not token or not supabase_url or not supabase_key:
        raise HTTPException(status_code=401, detail="Sign in required")

    request = UrlRequest(
        f"{supabase_url}/auth/v1/user",
        headers={"apikey": supabase_key, "Authorization": f"Bearer {token}"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            user = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired login session")
    if user.get("email", "").strip().lower() != expected_email.strip().lower():
        raise HTTPException(status_code=403, detail="You can only access your own documents")


@app.get("/")
def home():
    return {
        "project": "HigherUp.AI",
        "status": "running",
        "agent": "Skills Discovery",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/db-health")
def db_health():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT CURRENT_SCHEMA FROM DUMMY")
        schema = cursor.fetchone()[0]
        cursor.close()
        return {"status": "connected", "schema": schema}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(exc)[:300]}",
        )
    finally:
        if connection is not None:
            connection.close()


class SkillsRequest(BaseModel):
    candidate_text: str = Field(
        min_length=20,
        max_length=10000,
        description="Resume text or candidate-provided project evidence",
    )


@app.post("/skills/discover")
def discover_skills(request: SkillsRequest):
    return discover(request.candidate_text)

    skill_keywords = [
        "Python", "SQL", "Excel", "Power BI",
        "JavaScript", "Java", "C++", "HTML", "CSS",
        "communication", "leadership", "data analysis",
    ]

    found_skills = [
        skill for skill in skill_keywords
        if skill.lower() in text.lower()
    ]

    return {
        "agent": "Skills Discovery",
        "skills_found": found_skills,
        "evidence_source": "Candidate-provided text",
        "needs_candidate_review": True,
        "note": "Keyword-based prototype; AI extraction is not connected yet.",
    }


class CandidateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=255)
    headline: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    city: str | None = Field(default=None, max_length=100)
    looking_for: str | None = Field(default=None, max_length=100)
    available: str | None = Field(default=None, max_length=100)
    education: str | None = Field(default=None, max_length=250)
    linkedin: str | None = Field(default=None, max_length=500)
    github: str | None = Field(default=None, max_length=500)
    portfolio: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=1200)
    preferred_roles: str | None = Field(default=None, max_length=500)
    preferred_locations: str | None = Field(default=None, max_length=500)
    work_mode: str | None = Field(default=None, max_length=50)


@app.put("/candidates/by-email/{email}")
def upsert_candidate_by_email(email: str, request: CandidateRequest, http_request: Request):
    require_candidate_email(http_request.headers.get("Authorization"), email)
    if email.strip().lower() != request.email.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="Path email and body email must match"
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT CANDIDATE_ID FROM CANDIDATE_PROFILE WHERE LOWER(EMAIL) = ?",
            (request.email.strip().lower(),)
        )
        existing = cursor.fetchone()

        if existing:
            candidate_id = existing[0]

            cursor.execute(
                """
                UPDATE CANDIDATE_PROFILE
                SET FULL_NAME = ?, HEADLINE = COALESCE(?, HEADLINE),
                    PHONE = COALESCE(?, PHONE), CITY = COALESCE(?, CITY),
                    LOOKING_FOR = COALESCE(?, LOOKING_FOR),
                    AVAILABLE = COALESCE(?, AVAILABLE),
                    EDUCATION = COALESCE(?, EDUCATION),
                    LINKEDIN = COALESCE(?, LINKEDIN),
                    GITHUB = COALESCE(?, GITHUB),
                    PORTFOLIO = COALESCE(?, PORTFOLIO),
                    BIO = COALESCE(?, BIO),
                    PREFERRED_ROLES = COALESCE(?, PREFERRED_ROLES),
                    PREFERRED_LOCATIONS = COALESCE(?, PREFERRED_LOCATIONS),
                    WORK_MODE = COALESCE(?, WORK_MODE)
                WHERE CANDIDATE_ID = ?
                """,
                (
                    request.full_name,
                    request.headline,
                    request.phone,
                    request.city,
                    request.looking_for,
                    request.available,
                    request.education,
                    request.linkedin,
                    request.github,
                    request.portfolio,
                    request.bio,
                    request.preferred_roles,
                    request.preferred_locations,
                    request.work_mode,
                    candidate_id
                )
            )
            status = "updated"

        else:
            from uuid import uuid4
            candidate_id = str(uuid4())

            cursor.execute(
                """
                INSERT INTO CANDIDATE_PROFILE
                    (CANDIDATE_ID, FULL_NAME, EMAIL, HEADLINE, PHONE, CITY,
                     LOOKING_FOR, AVAILABLE, EDUCATION, LINKEDIN, GITHUB,
                     PORTFOLIO, BIO, PREFERRED_ROLES, PREFERRED_LOCATIONS,
                     WORK_MODE)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    request.full_name,
                    request.email.strip(),
                    request.headline or "",
                    request.phone or "",
                    request.city or "",
                    request.looking_for or "",
                    request.available or "",
                    request.education or "",
                    request.linkedin or "",
                    request.github or "",
                    request.portfolio or "",
                    request.bio or "",
                    request.preferred_roles or "",
                    request.preferred_locations or "",
                    request.work_mode or "Flexible"
                )
            )
            status = "created"

        connection.commit()

        return {
            "candidate_id": candidate_id,
            "status": status,
            "email": request.email
        }

    except Exception as exc:
        if connection is not None:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save candidate: {str(exc)[:300]}"
        )

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.get("/candidates/by-email/{email}")
def get_candidate_by_email(email: str, request: Request):
    require_candidate_email(request.headers.get("Authorization"), email)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT CANDIDATE_ID, FULL_NAME, EMAIL, HEADLINE, PHONE, CITY,
                   LOOKING_FOR, AVAILABLE, EDUCATION, LINKEDIN, GITHUB,
                   PORTFOLIO, BIO, PREFERRED_ROLES, PREFERRED_LOCATIONS,
                   WORK_MODE
            FROM CANDIDATE_PROFILE
            WHERE LOWER(EMAIL) = ?
            """,
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return {
            "candidate_id": row[0], "full_name": row[1], "email": row[2],
            "headline": row[3] or "", "phone": row[4] or "", "city": row[5] or "",
            "looking_for": row[6] or "", "available": row[7] or "",
            "education": row[8] or "", "linkedin": row[9] or "",
            "github": row[10] or "", "portfolio": row[11] or "", "bio": row[12] or "",
            "preferred_roles": row[13] or "", "preferred_locations": row[14] or "",
            "work_mode": row[15] or "Flexible",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve candidate: {str(exc)[:300]}"
        )
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
ALLOWED_DOCUMENT_KINDS = {"resume", "cover", "proof"}


@app.get("/candidates/by-email/{email}/documents")
def list_candidate_documents(email: str, request: Request):
    require_candidate_email(request.headers.get("Authorization"), email)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT D.DOCUMENT_ID, D.DOCUMENT_KIND, D.FILE_NAME,
                   D.CONTENT_TYPE, D.FILE_SIZE, D.UPLOADED_AT
            FROM CANDIDATE_DOCUMENT D
            JOIN CANDIDATE_PROFILE C ON C.CANDIDATE_ID = D.CANDIDATE_ID
            WHERE LOWER(C.EMAIL) = ?
            ORDER BY D.UPLOADED_AT DESC
            """,
            (email.strip().lower(),),
        )
        return [{
            "id": row[0], "kind": row[1], "name": row[2],
            "content_type": row[3], "size": row[4],
            "uploaded_at": row[5].isoformat() if row[5] else None,
        } for row in cursor.fetchall()]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not list documents: {str(exc)[:300]}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.post("/candidates/by-email/{email}/documents", status_code=201)
async def upload_candidate_document(email: str, request: Request):
    require_candidate_email(request.headers.get("Authorization"), email)
    kind = request.headers.get("X-Document-Kind", "").strip().lower()
    from urllib.parse import unquote
    name = unquote(request.headers.get("X-File-Name", "").strip())
    content_type = request.headers.get("Content-Type", "application/octet-stream")[:255]
    if kind not in ALLOWED_DOCUMENT_KINDS:
        raise HTTPException(status_code=400, detail="Unsupported document type")
    if not name or len(name) > 255 or "/" in name or "\\" in name or any(char in name for char in '\r\n"'):
        raise HTTPException(status_code=400, detail="Invalid file name")
    data = await request.body()
    if not data or len(data) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="File must be between 1 byte and 5 MB")

    connection = None
    cursor = None
    document_id = str(uuid4())
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT CANDIDATE_ID FROM CANDIDATE_PROFILE WHERE LOWER(EMAIL) = ?",
            (email.strip().lower(),),
        )
        candidate = cursor.fetchone()
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidate profile not found; save the profile first")
        cursor.execute(
            """
            INSERT INTO CANDIDATE_DOCUMENT
                (DOCUMENT_ID, CANDIDATE_ID, DOCUMENT_KIND, FILE_NAME,
                 CONTENT_TYPE, FILE_SIZE, FILE_DATA, UPLOADED_AT)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_UTCTIMESTAMP)
            """,
            (document_id, candidate[0], kind, name, content_type, len(data), data),
        )
        connection.commit()
        return {"id": document_id, "kind": kind, "name": name, "size": len(data), "status": "saved"}
    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not save document: {str(exc)[:300]}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.get("/candidates/by-email/{email}/documents/{document_id}")
def download_candidate_document(email: str, document_id: str, request: Request):
    require_candidate_email(request.headers.get("Authorization"), email)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT D.FILE_NAME, D.CONTENT_TYPE, D.FILE_DATA
            FROM CANDIDATE_DOCUMENT D
            JOIN CANDIDATE_PROFILE C ON C.CANDIDATE_ID = D.CANDIDATE_ID
            WHERE LOWER(C.EMAIL) = ? AND D.DOCUMENT_ID = ?
            """,
            (email.strip().lower(), document_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return Response(
            content=bytes(row[2]), media_type=row[1] or "application/octet-stream",
            headers={"Content-Disposition": f'inline; filename="{row[0]}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not retrieve document: {str(exc)[:300]}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.delete("/candidates/by-email/{email}/documents/{document_id}")
def delete_candidate_document(email: str, document_id: str, request: Request):
    require_candidate_email(request.headers.get("Authorization"), email)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            DELETE FROM CANDIDATE_DOCUMENT
            WHERE DOCUMENT_ID = ? AND CANDIDATE_ID = (
                SELECT CANDIDATE_ID FROM CANDIDATE_PROFILE WHERE LOWER(EMAIL) = ?
            )
            """,
            (document_id, email.strip().lower()),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        connection.commit()
        return {"id": document_id, "status": "deleted"}
    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        raise HTTPException(status_code=500, detail=f"Could not delete document: {str(exc)[:300]}")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()



@app.post("/candidates", status_code=201)
def create_candidate(request: CandidateRequest):
    candidate_id = str(uuid4())
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO CANDIDATE_PROFILE
                (CANDIDATE_ID, FULL_NAME, EMAIL,
                 PREFERRED_ROLES, PREFERRED_LOCATIONS, WORK_MODE)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                request.full_name,
                request.email,
                request.preferred_roles,
                request.preferred_locations,
                request.work_mode,
            ),
        )
        connection.commit()

        return {
            "candidate_id": candidate_id,
            "status": "created",
            "message": "Candidate profile saved.",
        }
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not save candidate: {str(exc)[:300]}",
        )
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT CANDIDATE_ID, FULL_NAME, EMAIL,
                   PREFERRED_ROLES, PREFERRED_LOCATIONS, WORK_MODE
            FROM CANDIDATE_PROFILE
            WHERE CANDIDATE_ID = ?
            """,
            (candidate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found",
            )

        return {
            "candidate_id": row[0],
            "full_name": row[1],
            "email": row[2],
            "preferred_roles": row[3],
            "preferred_locations": row[4],
            "work_mode": row[5],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve candidate: {str(exc)[:300]}",
        )
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


class EvidenceRequest(BaseModel):
    skill_name: str = Field(min_length=1, max_length=120)
    evidence_text: str = Field(default="", max_length=2000)
    evidence_type: str = Field(default="Candidate-provided", max_length=50)
    confidence_score: float | None = Field(default=None, ge=0, le=100)
    candidate_confirmed: bool = False


@app.post("/candidates/{candidate_id}/evidence", status_code=201)
def add_evidence(candidate_id: str, request: EvidenceRequest):
    evidence_id = str(uuid4())
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT CANDIDATE_ID FROM CANDIDATE_PROFILE WHERE CANDIDATE_ID = ?",
            (candidate_id,),
        )
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found; create the profile first.",
            )

        cursor.execute(
            """
            INSERT INTO SKILL_EVIDENCE
                (EVIDENCE_ID, CANDIDATE_ID, SKILL_NAME,
                 EVIDENCE_TEXT, EVIDENCE_TYPE,
                 CONFIDENCE_SCORE, CANDIDATE_CONFIRMED)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                candidate_id,
                request.skill_name,
                request.evidence_text,
                request.evidence_type,
                request.confidence_score,
                request.candidate_confirmed,
            ),
        )
        connection.commit()

        return {
            "evidence_id": evidence_id,
            "candidate_id": candidate_id,
            "status": "saved",
            "candidate_confirmed": request.candidate_confirmed,
        }
    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except Exception as exc:
        if connection is not None:
            connection.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Could not save evidence: {str(exc)[:300]}",
        )
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()
