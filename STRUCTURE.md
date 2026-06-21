# ResearchCrew — Project Structure

Multi-agent deep research system. Three Claude agents collaborate:
**Planner** (decomposes topic) → **Researcher ×N** (one per sub-question) →
**Writer** (synthesizes report). Includes a FastAPI web UI with live SSE
streaming, plus an offline **demo mode** that runs the full pipeline without an
API key.

```
researchcrew/
├── Dockerfile                  # python:3.11-slim; uvicorn on :8000
├── docker-compose.yml          # host 127.0.0.1:3003 → container :8000
├── pyproject.toml              # anthropic, fastapi, uvicorn, pydantic, rich, typer, tenacity
├── README.md
├── STRUCTURE.md                # this file
├── src/researchcrew/
│   ├── __init__.py
│   ├── config.py               # pydantic-settings: ANTHROPIC_API_KEY, claude_model
│   ├── models.py               # ResearchPlan, ResearchFinding, ResearchReport
│   ├── agents.py               # planner/researcher/writer using Claude tool_use
│   ├── crew.py                 # run_research() orchestration + rich CLI output
│   ├── demo.py                 # offline demo-mode report generator
│   ├── web.py                  # FastAPI app; UI at GET / + SSE research endpoint
│   └── ui/
│       └── index.html          # single-file dashboard (inline CSS+JS)
└── tests/
    ├── __init__.py
    ├── test_models.py
    └── test_web.py             # TestClient: / , /health, /api/research (SSE), /sync
```

## `src/researchcrew/` file reference

### `config.py`
`Settings(BaseSettings)` — `anthropic_api_key` (default `sk-placeholder`),
`claude_model` (default `claude-sonnet-4-6`), `max_research_rounds`. Reads
`.env`.

### `models.py`
Pydantic models: `ResearchPlan` (topic, sub_questions, scope, estimated_depth),
`ResearchFinding` (sub_question, key_points, confidence, limitations),
`ResearchReport` (title, executive_summary, findings, conclusions,
further_research, sources_note).

### `agents.py`
- `get_client()` — cached `anthropic.Anthropic` client.
- `planner_agent(topic) -> ResearchPlan` — tool-use `create_research_plan`.
- `researcher_agent(topic, sub_question, context) -> ResearchFinding` — tool-use
  `record_finding`.
- `writer_agent(plan, findings) -> ResearchReport` — tool-use `write_report`.
- All wrapped with `tenacity` retry (3 attempts, exp backoff).

### `crew.py`
- `run_research(topic) -> ResearchReport` — full CLI orchestration with rich
  progress UI. Stages: plan → research each sub-question → write.
- `print_report(report)` — rich terminal rendering.

### `demo.py`
- `is_demo_mode()` — True when the API key is placeholder/empty.
- `demo_plan/demo_finding/demo_report(topic)` — deterministic canned outputs so
  the UI works without credentials.

### `web.py` — FastAPI surface
- `app`, `ResearchRequest(BaseModel)`, `_sse(event, data)`.
- `GET  /`                    → serves `ui/index.html`
- `GET  /health`              → `{status, mode, model}` (mode = demo|live)
- `POST /api/research`        → SSE stream: events `start, plan, finding,
  report, done, error`. Transparently uses demo mode when no key.
- `POST /api/research/sync`   → non-streaming; returns full `ResearchReport`.

### `ui/index.html`
Vanilla dashboard (no CDN). Mars-red theme (`#C1440E`/`#f17b48`). Topic input
with example chips, three-stage progress (Planner/Researcher/Writer) driven by
SSE events, live-rendered findings as they stream, and a final formatted report
(summary, findings with confidence badges, conclusions, further research,
sources note). Demo-mode banner shown when no API key.

## How to run

**Local:**
```bash
pip install -e .
uvicorn researchcrew.web:app --reload
# UI:   http://localhost:8000/
# Docs: http://localhost:8000/docs
```

**Live mode** — set an API key in `.env` (copy `.env.example`):
```
ANTHROPIC_API_KEY=sk-ant-...
```

**Docker:**
```bash
docker compose up -d --build
# UI at http://127.0.0.1:3003/
```

**CLI (no web):**
```bash
researchcrew research "Diffusion models vs GANs" --output report.json
```

**Tests:**
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Notes
- Without `ANTHROPIC_API_KEY` the web UI and `/sync` run in **demo mode** (fully
  interactive, deterministic canned output). The planet is still "live".
- The SSE endpoint uses `text/event-stream`; the frontend reads it via the
  Fetch streaming API and splits on `\n\n` frame boundaries.
