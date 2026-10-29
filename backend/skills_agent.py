"""Include.AI - Skills Discovery Agent (SAP Generative AI Hub).

Reads candidate text and returns skills WITH evidence quotes and confidence.
Rules: never invent skills, quotes must exist in the text, ignore protected
attributes, and every result still needs the candidate's confirmation.
"""
import json
import os
import re

MODEL = os.getenv("AICORE_MODEL", "gpt-5-mini")  # must match a deployment in your AI Launchpad

SYSTEM_PROMPT = """You are the Skills Discovery Agent for a skills-first hiring platform.
Extract job-relevant skills from the candidate's text.

Rules:
- Only list a skill if the text supports it. Never invent or assume skills.
- For each skill give "evidence": a SHORT quote copied EXACTLY from the text.
- "evidence_type" is one of: project, internship, work, freelance, hackathon,
  course, certification, informal, self-reported.
- "confidence" is 0-100: high only for concrete proof (a built project, work done),
  low for a bare mention in a skills list.
- Include transferable skills from informal work or career breaks (e.g. managing
  household budgets, volunteering, running a small business) when clearly stated.
- Ignore and never output gender, age, caste, religion, disability, college name
  or degree status.
Return ONLY valid JSON, no markdown:
{"skills":[{"skill":"","evidence":"","evidence_type":"","confidence":0}]}"""


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _call_llm(text: str) -> str:
    # Imported here so .env is already loaded and the app still boots without the SDK.
    from gen_ai_hub.proxy.native.openai import chat

    response = chat.completions.create(
        model_name=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        # GPT-5 reasoning models: no temperature setting, and the budget also
        # covers hidden reasoning tokens, so keep it generous.
        max_completion_tokens=4000,
    )
    return response.choices[0].message.content


def _parse_json(raw: str) -> list[dict]:
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(raw).get("skills", [])


def _llm_discover(text: str) -> list[dict]:
    source = _norm(text)
    results, seen = [], set()
    for item in _parse_json(_call_llm(text)):
        name = str(item.get("skill", "")).strip()
        quote = str(item.get("evidence", "")).strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        # Grounding check: the quote must really appear in the candidate's text.
        grounded = bool(quote) and _norm(quote) in source
        try:
            confidence = max(0, min(100, int(item.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0
        if not grounded:
            confidence = min(confidence, 30)

        results.append({
            "skill_name": name,
            "evidence_text": quote if grounded else "",
            "evidence_type": str(item.get("evidence_type", "self-reported"))[:50],
            "confidence_score": confidence,
            "evidence_verified_in_text": grounded,
            "candidate_confirmed": False,
        })
    return results


KEYWORDS = [
    "Python", "SQL", "Excel", "Power BI", "JavaScript", "Java", "C++",
    "HTML", "CSS", "communication", "leadership", "data analysis",
]


def _keyword_discover(text: str) -> list[dict]:
    results = []
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    for kw in KEYWORDS:
        # Word-boundary match so "Java" does not match "JavaScript".
        pattern = r"(?<![A-Za-z0-9+#])" + re.escape(kw) + r"(?![A-Za-z0-9+#])"
        match = next((s for s in sentences if re.search(pattern, s, re.I)), None)
        if match:
            results.append({
                "skill_name": kw,
                "evidence_text": match.strip()[:300],
                "evidence_type": "self-reported",
                "confidence_score": 40,
                "evidence_verified_in_text": True,
                "candidate_confirmed": False,
            })
    return results


def discover(text: str) -> dict:
    mode, note = "sap_generative_ai_hub", "AI-extracted. Review every item before it counts."
    try:
        skills = _llm_discover(text)
    except Exception as exc:  # no credentials, no deployment, bad JSON, network...
        skills = _keyword_discover(text)
        mode = "keyword_fallback"
        note = f"AI extraction unavailable ({type(exc).__name__}); used keyword matching."

    return {
        "agent": "Skills Discovery",
        "mode": mode,
        "skills": skills,
        "needs_candidate_review": True,
        "note": note,
    }