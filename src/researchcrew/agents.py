import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import settings
from .models import ResearchPlan, ResearchFinding, ResearchReport

_client: anthropic.Anthropic | None = None

def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def planner_agent(topic: str) -> ResearchPlan:
    """Decomposes a research topic into structured sub-questions."""
    client = get_client()
    tools = [{
        "name": "create_research_plan",
        "description": "Create a structured research plan with sub-questions",
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_questions": {"type": "array", "items": {"type": "string"}, "description": "3-5 focused sub-questions"},
                "scope": {"type": "string", "description": "Brief scope description"},
                "estimated_depth": {"type": "string", "enum": ["surface", "moderate", "deep"]},
            },
            "required": ["sub_questions", "scope", "estimated_depth"],
        },
    }]
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1024,
        system="You are a research planner. Break down complex topics into focused, answerable sub-questions.",
        messages=[{"role": "user", "content": f"Create a research plan for: {topic}"}],
        tools=tools,
        tool_choice={"type": "tool", "name": "create_research_plan"},
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    inp = tool_use.input
    return ResearchPlan(topic=topic, **inp)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def researcher_agent(topic: str, sub_question: str, context: str = "") -> ResearchFinding:
    """Researches a specific sub-question and returns structured findings."""
    client = get_client()
    tools = [{
        "name": "record_finding",
        "description": "Record research findings for a sub-question",
        "input_schema": {
            "type": "object",
            "properties": {
                "key_points": {"type": "array", "items": {"type": "string"}, "description": "3-6 key findings"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "limitations": {"type": "string", "description": "Any limitations or caveats"},
            },
            "required": ["key_points", "confidence"],
        },
    }]
    ctx_str = f"\n\nContext from previous findings:\n{context}" if context else ""
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=f"You are an expert researcher on: {topic}. Provide accurate, specific, and well-reasoned findings.",
        messages=[{"role": "user", "content": f"Research this question thoroughly: {sub_question}{ctx_str}"}],
        tools=tools,
        tool_choice={"type": "tool", "name": "record_finding"},
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    inp = tool_use.input
    return ResearchFinding(sub_question=sub_question, **inp)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def writer_agent(plan: ResearchPlan, findings: list[ResearchFinding]) -> ResearchReport:
    """Synthesizes findings into a polished research report."""
    client = get_client()
    tools = [{
        "name": "write_report",
        "description": "Write the final research report",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "executive_summary": {"type": "string", "description": "2-3 paragraph summary"},
                "conclusions": {"type": "array", "items": {"type": "string"}, "description": "3-5 main conclusions"},
                "further_research": {"type": "array", "items": {"type": "string"}, "description": "2-4 areas for further research"},
            },
            "required": ["title", "executive_summary", "conclusions", "further_research"],
        },
    }]
    findings_text = "\n\n".join(
        f"Sub-question: {f.sub_question}\nKey points:\n" + "\n".join(f"  - {p}" for p in f.key_points)
        for f in findings
    )
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system="You are a research writer. Synthesize findings into a clear, well-structured report.",
        messages=[{"role": "user", "content": f"Topic: {plan.topic}\n\nFindings:\n{findings_text}\n\nWrite a comprehensive research report."}],
        tools=tools,
        tool_choice={"type": "tool", "name": "write_report"},
    )
    tool_use = next(b for b in response.content if b.type == "tool_use")
    inp = tool_use.input
    return ResearchReport(findings=findings, **inp)
