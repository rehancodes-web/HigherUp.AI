"""Talent pool API (included by main.py).

Recruiters add resumes (PDF, Word or text). The AI reads each one and writes a one-page summary,
which is stored in SAP HANA and shown in the Talent Deck. Tables: see 004_talent_profiles.sql
"""
import json
from urllib.parse import unquote
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from interviews import db, require_role, run_db
from resume_summary import ResumeReadError, extract_resume_text, summarize_resume

router = APIRouter(prefix="/talent", tags=["talent"])
MAX_RESUME_BYTES = 5 * 1024 * 1024


def save_profile(cursor, profile: dict) -> dict:
    """Insert the profile, or replace the one made from the same file name. Returns the profile with its id."""
    cursor.execute("SELECT PROFILE_ID FROM TALENT_PROFILE WHERE SOURCE_FILE = ?", (profile["source"],))
    existing = cursor.fetchone()
    profile_id = existing[0] if existing else str(uuid4())
    profile = {**profile, "id": profile_id}
    payload = json.dumps(profile, ensure_ascii=False).encode("utf-8")
    if existing:
        cursor.execute(
            "UPDATE TALENT_PROFILE SET CANDIDATE_NAME = ?, PROFILE_JSON = ?, CREATED_AT = CURRENT_UTCTIMESTAMP WHERE PROFILE_ID = ?",
            (profile["name"], payload, profile_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO TALENT_PROFILE (PROFILE_ID, SOURCE_FILE, CANDIDATE_NAME, PROFILE_JSON, CREATED_AT)
            VALUES (?, ?, ?, ?, CURRENT_UTCTIMESTAMP)
            """,
            (profile_id, profile["source"], profile["name"], payload),
        )
    return profile


@router.get("")
def list_profiles(request: Request):
    require_role(request.headers.get("Authorization"), "recruiter")

    def work():
        with db() as cursor:
            cursor.execute("SELECT PROFILE_ID, PROFILE_JSON FROM TALENT_PROFILE ORDER BY CREATED_AT, PROFILE_ID")
            profiles = []
            for profile_id, blob in cursor.fetchall():
                profile = json.loads(bytes(blob).decode("utf-8"))
                profile["id"] = profile_id
                profiles.append(profile)
            return {"profiles": profiles}
    return run_db("load the talent pool", work)


@router.post("/resumes", status_code=201)
async def add_resume(request: Request):
    """Body = the resume file. The file name goes in X-File-Name. The AI reads it and a profile is saved."""
    require_role(request.headers.get("Authorization"), "recruiter")
    name = unquote(request.headers.get("X-File-Name", "")).strip()
    if not name or len(name) > 255 or "/" in name or "\\" in name:
        raise HTTPException(status_code=400, detail="Invalid file name")
    data = await request.body()
    if not data or len(data) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="The resume must be between 1 byte and 5 MB")
    try:
        text = await run_in_threadpool(extract_resume_text, data, name)
    except ResumeReadError as exc:
        status = 415 if str(exc).startswith("Unsupported") else 422
        raise HTTPException(status_code=status, detail=str(exc))
    profile = await run_in_threadpool(summarize_resume, text, name)   # the AI call can take a few seconds

    def work():
        with db() as cursor:
            return save_profile(cursor, profile)
    return {"profile": await run_in_threadpool(run_db, "save the profile", work)}


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=40, max_length=30_000)
    source: str = Field(default="pasted text", max_length=255)


@router.post("/summarize")
async def summarize_text(body: SummarizeRequest, request: Request):
    """Summarise pasted resume text without saving it (handy for trying the AI)."""
    require_role(request.headers.get("Authorization"), "recruiter")
    return {"profile": await run_in_threadpool(summarize_resume, body.text, body.source)}


@router.delete("/{profile_id}")
def delete_profile(profile_id: str, request: Request):
    require_role(request.headers.get("Authorization"), "recruiter")

    def work():
        with db() as cursor:
            cursor.execute("DELETE FROM TALENT_PROFILE WHERE PROFILE_ID = ?", (profile_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Profile not found")
            return {"id": profile_id, "status": "deleted"}
    return run_db("remove the profile", work)
