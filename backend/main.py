from fastapi import FastAPI

app = FastAPI(title="Include.AI API")

@app.get("/")
def home():
    return {
        "project": "Include.AI",
        "status": "running",
        "agent": "Skills Discovery"
    }

@app.get("/health")
def health():
    return {"status": "healthy"} 


from pydantic import BaseModel, Field

class SkillsRequest(BaseModel):
    candidate_text: str = Field(
        min_length=20,
        max_length=10000,
        description="Resume text or candidate-provided project evidence"
    )

@app.post("/skills/discover")
def discover_skills(request: SkillsRequest):
    text = request.candidate_text

    skill_keywords = [
        "Python", "SQL", "Excel", "Power BI",
        "JavaScript", "Java", "C++", "HTML", "CSS",
        "communication", "leadership", "data analysis"
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
        "note": "Keyword-based prototype; AI extraction is not connected yet."
    }
