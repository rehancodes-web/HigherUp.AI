"""Interview scheduling API (included by main.py).

Recruiter: add/remove interview slots, select a shortlisted candidate (sends an invite).
Candidate: read invites from the HigherUp.AI assistant and book one open slot.
Tables: see 003_interviews.sql
"""
import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, date as date_cls
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest, urlopen
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/interviews", tags=["interviews"])


def get_supabase_user(authorization: str | None) -> dict:
    """Verify a Supabase access token and return its email, role, name and company."""
    token = (authorization or "").removeprefix("Bearer ").strip()
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Server is missing SUPABASE_URL or SUPABASE_PUBLISHABLE_KEY")
    if not token:
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
    meta = user.get("user_metadata") or {}
    email = (user.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Account has no email")
    return {
        "email": email,
        "role": "recruiter" if meta.get("role") == "recruiter" else "candidate",
        "name": meta.get("full_name") or email,
        "company": meta.get("company") or meta.get("company_name") or meta.get("organization") or os.getenv("RECRUITER_COMPANY", "Vergemount"),
    }


def require_role(authorization: str | None, role: str) -> dict:
    user = get_supabase_user(authorization)
    if user["role"] != role:
        raise HTTPException(status_code=403, detail=f"Only {role} accounts can do this")
    return user


@contextmanager
def db():
    """Open a HANA connection + cursor, commit on success, roll back on error."""
    from main import get_db_connection  # imported here to avoid a circular import

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def run_db(action: str, fn):
    """Run a DB function and turn unexpected errors into a readable 500."""
    try:
        return fn()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not {action}: {str(exc)[:300]}")


def slot_label(slot_date: str, slot_time: str) -> str:
    """'2026-11-05', '14:30' -> 'Thu, 5 Nov, 2:30 pm' (matches the front end)."""
    d = datetime.strptime(f"{slot_date} {slot_time}", "%Y-%m-%d %H:%M")
    hour = d.hour % 12 or 12
    return f"{d:%a}, {d.day} {d:%b}, {hour}:{d:%M} {'am' if d.hour < 12 else 'pm'}"


def iso(value) -> str | None:
    return value.isoformat() + "Z" if value else None


def minutes(hhmm: str) -> int:
    hours, mins = hhmm.split(":")
    return int(hours) * 60 + int(mins)


def slot_conflicts(cursor, recruiter: str, slot_date: str, slot_time: str, length: int, extra=()) -> bool:
    """True if [time, time+length) overlaps a slot this recruiter already has that day (or one in `extra`)."""
    cursor.execute(
        "SELECT SLOT_TIME, LENGTH_MIN FROM INTERVIEW_SLOT WHERE RECRUITER_EMAIL = ? AND SLOT_DATE = ?",
        (recruiter, slot_date),
    )
    start = minutes(slot_time)
    end = start + length
    for other_time, other_length in list(cursor.fetchall()) + list(extra):
        other_start = minutes(other_time)
        if start < other_start + other_length and other_start < end:
            return True
    return False


def mode_text(mode: str) -> str:
    return {"Offline": "Offline (in person)"}.get(mode, mode)


SLOT_SELECT = """
    SELECT S.SLOT_ID, S.SLOT_DATE, S.SLOT_TIME, S.LENGTH_MIN, S.MODE, S.INTERVIEWER, I.CANDIDATE_NAME, S.RECRUITER_EMAIL
    FROM INTERVIEW_SLOT S
    LEFT JOIN INTERVIEW_INVITE I ON I.INVITE_ID = S.BOOKED_INVITE_ID
"""


def slot_json(row) -> dict:
    return {
        "id": row[0], "date": row[1], "time": row[2], "length": row[3],
        "mode": row[4], "with": row[5] or "", "bookedBy": row[6], "recruiter": row[7],
    }


def load_invites(cursor, where: str, params: tuple) -> list[dict]:
    cursor.execute(
        f"""
        SELECT INVITE_ID, CANDIDATE_NAME, HEADLINE, COMPANY, ROLE_TITLE, SLOT_ID, IS_READ, CREATED_AT, RECRUITER_EMAIL
        FROM INTERVIEW_INVITE WHERE {where} ORDER BY CREATED_AT
        """,
        params,
    )
    invites = [{
        "id": r[0], "candidate": r[1], "headline": r[2] or "", "company": r[3], "role": r[4],
        "slotId": r[5], "read": bool(r[6]), "sentAt": iso(r[7]), "recruiter": r[8], "messages": [],
    } for r in cursor.fetchall()]
    if invites:
        by_id = {inv["id"]: inv for inv in invites}
        marks = ",".join("?" for _ in invites)
        cursor.execute(
            f"""
            SELECT INVITE_ID, SENDER, BODY, SHOW_SLOTS, CREATED_AT FROM INTERVIEW_MESSAGE
            WHERE INVITE_ID IN ({marks}) ORDER BY INVITE_ID, SEQ_NO
            """,
            tuple(by_id),
        )
        for r in cursor.fetchall():
            by_id[r[0]]["messages"].append({"from": r[1], "text": r[2], "slots": bool(r[3]), "at": iso(r[4])})
    # When the candidate booked = the time of their "I'll take ..." message (shown to the recruiter).
    for inv in invites:
        booked_at = next((m["at"] for m in inv["messages"] if m["from"] == "you"), None)
        inv["bookedAt"] = booked_at if inv["slotId"] else None
    return invites


def add_message(cursor, invite_id: str, sender: str, body: str, show_slots: bool = False) -> None:
    cursor.execute("SELECT COUNT(*) FROM INTERVIEW_MESSAGE WHERE INVITE_ID = ?", (invite_id,))
    seq = cursor.fetchone()[0] + 1
    cursor.execute(
        """
        INSERT INTO INTERVIEW_MESSAGE (MESSAGE_ID, INVITE_ID, SEQ_NO, SENDER, BODY, SHOW_SLOTS, CREATED_AT)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_UTCTIMESTAMP)
        """,
        (str(uuid4()), invite_id, seq, sender, body[:1000], show_slots),
    )


class SlotRequest(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(pattern=r"^\d{2}:\d{2}$")
    length: int = Field(default=45, ge=15, le=180)
    mode: str = Field(default="Video call", max_length=30)
    with_: str | None = Field(default=None, alias="with", max_length=120)


class InviteRequest(BaseModel):
    candidate: str = Field(min_length=1, max_length=120)
    candidate_email: str | None = Field(default=None, max_length=255)
    headline: str | None = Field(default=None, max_length=200)
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)


class BookRequest(BaseModel):
    slot_id: str = Field(min_length=1, max_length=36)


@router.get("")
def recruiter_interviews(request: Request):
    """Recruiter view: this recruiter's slots and the invites they have sent."""
    user = require_role(request.headers.get("Authorization"), "recruiter")

    def work():
        with db() as cursor:
            cursor.execute(SLOT_SELECT + " WHERE S.RECRUITER_EMAIL = ? ORDER BY S.SLOT_DATE, S.SLOT_TIME", (user["email"],))
            slots = [slot_json(r) for r in cursor.fetchall()]
            invites = load_invites(cursor, "RECRUITER_EMAIL = ?", (user["email"],))
            return {"slots": slots, "invites": invites}
    return run_db("load interviews", work)


@router.post("/slots", status_code=201)
def create_slot(body: SlotRequest, request: Request):
    user = require_role(request.headers.get("Authorization"), "recruiter")
    try:
        when = datetime.strptime(f"{body.date} {body.time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time")
    if when.date() < date_cls.today():
        raise HTTPException(status_code=400, detail="That date has already passed")

    def work():
        with db() as cursor:
            if slot_conflicts(cursor, user["email"], body.date, body.time, body.length):
                raise HTTPException(status_code=409, detail="That time overlaps a slot you already added")
            slot_id = str(uuid4())
            interviewer = (body.with_ or "").strip()
            cursor.execute(
                """
                INSERT INTO INTERVIEW_SLOT
                    (SLOT_ID, RECRUITER_EMAIL, SLOT_DATE, SLOT_TIME, LENGTH_MIN, MODE, INTERVIEWER, BOOKED_INVITE_ID, CREATED_AT)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, CURRENT_UTCTIMESTAMP)
                """,
                (slot_id, user["email"], body.date, body.time, body.length, body.mode, interviewer),
            )
            return {"id": slot_id, "date": body.date, "time": body.time, "length": body.length,
                    "mode": body.mode, "with": interviewer, "bookedBy": None, "recruiter": user["email"]}
    return run_db("add slot", work)


class BulkSlotRequest(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    length: int = Field(default=45, ge=15, le=180)
    mode: str = Field(default="Video call", max_length=30)
    with_: str | None = Field(default=None, alias="with", max_length=120)
    times: list[str] = Field(min_length=1, max_length=48)


@router.post("/slots/bulk", status_code=201)
def create_slots_bulk(body: BulkSlotRequest, request: Request):
    """Publish several start times for one day in one go (all or nothing)."""
    user = require_role(request.headers.get("Authorization"), "recruiter")
    try:
        day = datetime.strptime(body.date, "%Y-%m-%d").date()
        times = sorted({datetime.strptime(t, "%H:%M").strftime("%H:%M") for t in body.times})
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time")
    if day < date_cls.today():
        raise HTTPException(status_code=400, detail="That date has already passed")
    interviewer = (body.with_ or "").strip()

    def work():
        with db() as cursor:
            added, pending = [], []
            for slot_time in times:
                if slot_conflicts(cursor, user["email"], body.date, slot_time, body.length, extra=pending):
                    raise HTTPException(status_code=409, detail=f"{slot_time} overlaps a slot you already added")
                slot_id = str(uuid4())
                cursor.execute(
                    """
                    INSERT INTO INTERVIEW_SLOT
                        (SLOT_ID, RECRUITER_EMAIL, SLOT_DATE, SLOT_TIME, LENGTH_MIN, MODE, INTERVIEWER, BOOKED_INVITE_ID, CREATED_AT)
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, CURRENT_UTCTIMESTAMP)
                    """,
                    (slot_id, user["email"], body.date, slot_time, body.length, body.mode, interviewer),
                )
                pending.append((slot_time, body.length))
                added.append({"id": slot_id, "date": body.date, "time": slot_time, "length": body.length,
                              "mode": body.mode, "with": interviewer, "bookedBy": None, "recruiter": user["email"]})
            return {"slots": added}
    return run_db("add slots", work)


@router.delete("/slots/{slot_id}")
def delete_slot(slot_id: str, request: Request):
    user = require_role(request.headers.get("Authorization"), "recruiter")

    def work():
        with db() as cursor:
            cursor.execute(
                "DELETE FROM INTERVIEW_SLOT WHERE SLOT_ID = ? AND RECRUITER_EMAIL = ? AND BOOKED_INVITE_ID IS NULL",
                (slot_id, user["email"]),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Slot not found or already booked")
            return {"id": slot_id, "status": "deleted"}
    return run_db("remove slot", work)


@router.post("/invites", status_code=201)
def create_invite(body: InviteRequest, request: Request):
    """Recruiter selects a shortlisted candidate: the assistant sends them a Round 1 invite."""
    user = require_role(request.headers.get("Authorization"), "recruiter")
    candidate_email = (body.candidate_email or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", candidate_email):
        raise HTTPException(status_code=400, detail="Enter the email of the candidate account that should get this invite")

    def work():
        with db() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM INTERVIEW_INVITE WHERE RECRUITER_EMAIL = ? AND CANDIDATE_NAME = ? AND ROLE_TITLE = ?",
                (user["email"], body.candidate, body.role),
            )
            if cursor.fetchone()[0]:
                raise HTTPException(status_code=409, detail=f"{body.candidate} has already been invited")
            cursor.execute(
                "SELECT COUNT(*) FROM INTERVIEW_SLOT WHERE RECRUITER_EMAIL = ? AND BOOKED_INVITE_ID IS NULL",
                (user["email"],),
            )
            open_slots = cursor.fetchone()[0]
            invite_id = str(uuid4())
            cursor.execute(
                """
                INSERT INTO INTERVIEW_INVITE
                    (INVITE_ID, RECRUITER_EMAIL, CANDIDATE_NAME, CANDIDATE_EMAIL, HEADLINE, COMPANY, ROLE_TITLE, SLOT_ID, IS_READ, CREATED_AT)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, FALSE, CURRENT_UTCTIMESTAMP)
                """,
                (invite_id, user["email"], body.candidate, candidate_email, body.headline or "", body.company, body.role),
            )
            first = body.candidate.split()[0]
            add_message(cursor, invite_id, "ai",
                        f"Hi {first}, congratulations! You have been shortlisted for a Round 1 interview "
                        f"at {body.company} for the {body.role} role.")
            # show_slots=True marks the message that carries the "Go to Selections" button.
            add_message(cursor, invite_id, "ai",
                        "Go to Selections in your workspace and pick an interview time that works for you.",
                        show_slots=True)
            invites = load_invites(cursor, "INVITE_ID = ?", (invite_id,))
            return {"invite": invites[0], "openSlots": open_slots}
    return run_db("send invite", work)


@router.get("/inbox")
def candidate_inbox(request: Request):
    """Candidate view: invites addressed to them (plus demo invites with no email) and the open slots they can pick."""
    user = require_role(request.headers.get("Authorization"), "candidate")

    def work():
        with db() as cursor:
            invites = load_invites(cursor, "LOWER(CANDIDATE_EMAIL) = ?", (user["email"],))
            recruiters = sorted({inv["recruiter"] for inv in invites})
            slots = []
            if recruiters:
                marks = ",".join("?" for _ in recruiters)
                booked = [inv["slotId"] for inv in invites if inv["slotId"]]
                booked_sql = f" OR S.SLOT_ID IN ({','.join('?' for _ in booked)})" if booked else ""
                cursor.execute(
                    SLOT_SELECT + f" WHERE (S.RECRUITER_EMAIL IN ({marks}) AND S.BOOKED_INVITE_ID IS NULL){booked_sql}"
                    " ORDER BY S.SLOT_DATE, S.SLOT_TIME",
                    tuple(recruiters) + tuple(booked),
                )
                slots = [slot_json(r) for r in cursor.fetchall()]
            # Each invite only offers its own recruiter's slots ("recruiter" is on both).
            return {"slots": slots, "invites": invites}
    return run_db("load inbox", work)


@router.post("/inbox/read")
def mark_inbox_read(request: Request):
    user = require_role(request.headers.get("Authorization"), "candidate")

    def work():
        with db() as cursor:
            cursor.execute(
                "UPDATE INTERVIEW_INVITE SET IS_READ = TRUE WHERE IS_READ = FALSE AND LOWER(CANDIDATE_EMAIL) = ?",
                (user["email"],),
            )
            return {"status": "ok"}
    return run_db("update inbox", work)


@router.post("/invites/{invite_id}/book")
def book_slot(invite_id: str, body: BookRequest, request: Request):
    """Candidate picks a slot. The slot is claimed atomically, so two people can't book the same time."""
    user = require_role(request.headers.get("Authorization"), "candidate")

    def work():
        with db() as cursor:
            cursor.execute(
                """
                SELECT RECRUITER_EMAIL, COMPANY, SLOT_ID FROM INTERVIEW_INVITE
                WHERE INVITE_ID = ? AND LOWER(CANDIDATE_EMAIL) = ?
                """,
                (invite_id, user["email"]),
            )
            invite = cursor.fetchone()
            if invite is None:
                raise HTTPException(status_code=404, detail="Invite not found")
            if invite[2]:
                raise HTTPException(status_code=409, detail="You have already booked an interview for this invite")
            cursor.execute(
                """
                UPDATE INTERVIEW_SLOT SET BOOKED_INVITE_ID = ?
                WHERE SLOT_ID = ? AND RECRUITER_EMAIL = ? AND BOOKED_INVITE_ID IS NULL
                """,
                (invite_id, body.slot_id, invite[0]),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=409, detail="Sorry, that slot was just taken. Please pick another.")
            cursor.execute("UPDATE INTERVIEW_INVITE SET SLOT_ID = ? WHERE INVITE_ID = ?", (body.slot_id, invite_id))
            cursor.execute(
                "SELECT SLOT_DATE, SLOT_TIME, LENGTH_MIN, MODE, INTERVIEWER FROM INTERVIEW_SLOT WHERE SLOT_ID = ?",
                (body.slot_id,),
            )
            s = cursor.fetchone()
            label = slot_label(s[0], s[1])
            add_message(cursor, invite_id, "you", f"I'll take {label}.")
            add_message(cursor, invite_id, "ai",
                        f"You're booked! Round 1 interview at {invite[1]} on {label} "
                        f"({s[2]} min, {mode_text(s[3])}{' with ' + s[4] if s[4] else ''}). Good luck!")
            return {"status": "booked", "slot_id": body.slot_id, "label": label}
    return run_db("book slot", work)
