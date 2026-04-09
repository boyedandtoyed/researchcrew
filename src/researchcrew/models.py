from pydantic import BaseModel
from typing import Optional

class ResearchPlan(BaseModel):
    topic: str
    sub_questions: list[str]
    scope: str
    estimated_depth: str  # "surface" | "moderate" | "deep"

class ResearchFinding(BaseModel):
    sub_question: str
    key_points: list[str]
    confidence: str  # "high" | "medium" | "low"
    limitations: Optional[str] = None

class ResearchReport(BaseModel):
    title: str
    executive_summary: str
    findings: list[ResearchFinding]
    conclusions: list[str]
    further_research: list[str]
    sources_note: str = "Research based on Claude's training knowledge up to August 2025."
