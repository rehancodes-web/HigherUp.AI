
import os
from pathlib import Path
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from hdbcli import dbapi
from skills_agent import discover

# Load the .env located beside main.py
load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Include.AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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


@app.get("/")
def home():
    return {
        "project": "Include.AI",
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
    headline: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=40)
    city: str = Field(default="", max_length=100)
    looking_for: str = Field(default="", max_length=100)
    available: str = Field(default="", max_length=100)
    education: str = Field(default="", max_length=250)
    linkedin: str = Field(default="", max_length=500)
    github: str = Field(default="", max_length=500)
    portfolio: str = Field(default="", max_length=500)
    bio: str = Field(default="", max_length=1200)
    preferred_roles: str = Field(default="", max_length=500)
    preferred_locations: str = Field(default="", max_length=500)
    work_mode: str = Field(default="Flexible", max_length=50)


@app.put("/candidates/by-email/{email}")
def upsert_candidate_by_email(email: str, request: CandidateRequest):
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
                SET FULL_NAME = ?, HEADLINE = ?, PHONE = ?, CITY = ?,
                    LOOKING_FOR = ?, AVAILABLE = ?, EDUCATION = ?,
                    LINKEDIN = ?, GITHUB = ?, PORTFOLIO = ?, BIO = ?,
                    PREFERRED_ROLES = ?, PREFERRED_LOCATIONS = ?, WORK_MODE = ?
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
                    request.work_mode
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
def get_candidate_by_email(email: str):
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
