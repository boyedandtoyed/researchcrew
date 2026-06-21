"""FastAPI web layer for ResearchCrew — serves the dashboard UI and a streaming research endpoint.

The web app reuses the existing agent pipeline (planner → researcher → writer).
When no API key is configured it transparently falls back to the offline demo
mode so the UI is always interactive.
"""
from __future__ import annotations
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from . import demo
from .agents import planner_agent, researcher_agent, writer_agent
from .config import settings
from .models import ResearchReport

app = FastAPI(title="ResearchCrew", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_UI = Path(__file__).parent / "ui" / "index.html"


@app.get("/", include_in_schema=False)
def index():
    """Serve the single-page web UI dashboard."""
    return FileResponse(_UI)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "researchcrew",
        "version": "0.1.0",
        "mode": "demo" if demo.is_demo_mode() else "live",
        "model": settings.claude_model,
    }


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=400)


def _sse(event: str, data: dict) -> str:
    """Format a single Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.post("/api/research")
def research(req: ResearchRequest):
    """Run the research crew, streaming stage events via SSE.

    Events:
      - plan        : the planner's ResearchPlan
      - finding     : one ResearchFinding (one per sub-question)
      - report      : the final ResearchReport
      - done        : terminal
      - error       : terminal, with a message
    """
    topic = req.topic.strip()

    def event_stream():
        try:
            yield _sse("start", {"topic": topic, "mode": "demo" if demo.is_demo_mode() else "live"})
            if demo.is_demo_mode():
                plan = demo.demo_plan(topic)
                yield _sse("plan", plan.model_dump())
                findings = []
                for i, q in enumerate(plan.sub_questions, 1):
                    finding = demo.demo_finding(topic, q)
                    findings.append(finding)
                    yield _sse("finding", {"index": i, "total": len(plan.sub_questions), "finding": finding.model_dump()})
                report = demo.demo_report(topic)
                report.findings = findings
                yield _sse("report", report.model_dump())
                yield _sse("done", {"demo": True})
                return

            # Live mode: real Claude agents
            plan = planner_agent(topic)
            yield _sse("plan", plan.model_dump())

            findings = []
            context = ""
            for i, q in enumerate(plan.sub_questions, 1):
                finding = researcher_agent(topic, q, context=context)
                findings.append(finding)
                context += f"\n{q}: {'; '.join(finding.key_points[:2])}"
                yield _sse("finding", {"index": i, "total": len(plan.sub_questions), "finding": finding.model_dump()})

            report = writer_agent(plan, findings)
            yield _sse("report", report.model_dump())
            yield _sse("done", {"demo": False})
        except Exception as e:  # noqa: BLE001 - surface any failure as an SSE error event
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/research/sync", response_model=ResearchReport)
def research_sync(req: ResearchRequest) -> ResearchReport:
    """Non-streaming convenience endpoint — returns the full report at once."""
    topic = req.topic.strip()
    if demo.is_demo_mode():
        return demo.demo_report(topic)
    plan = planner_agent(topic)
    findings = []
    context = ""
    for q in plan.sub_questions:
        finding = researcher_agent(topic, q, context=context)
        findings.append(finding)
        context += f"\n{q}: {'; '.join(finding.key_points[:2])}"
    return writer_agent(plan, findings)
