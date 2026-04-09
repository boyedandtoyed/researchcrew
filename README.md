# ResearchCrew

Multi-agent deep research system powered by Claude. Three specialized agents collaborate to plan, research, and synthesize comprehensive reports on any topic.

## Agent Architecture

```
Topic → [Planner] → Sub-questions → [Researcher × N] → Findings → [Writer] → Report
```

- **Planner** — decomposes topic, defines scope, creates 3-5 sub-questions
- **Researcher** — investigates each sub-question, records findings + confidence
- **Writer** — synthesizes all findings into a structured report

All agents use Claude's `tool_use` for structured JSON outputs.

## Installation & Running

### Prerequisites
- Python 3.11+
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### Quick Start
```bash
git clone https://github.com/boyedandtoyed/researchcrew.git
cd researchcrew

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .

cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

# Run research
researchcrew research "The impact of transformer architecture on modern NLP"

# Save report to JSON
researchcrew research "Diffusion models vs GANs" --output report.json
```

### Python API
```python
from researchcrew.crew import run_research, print_report

report = run_research("Attention mechanisms in transformers")
print_report(report)
print(f"Found {len(report.findings)} research findings")
```

### Running Tests
```bash
pytest tests/ -v
```

## Tech Stack
Anthropic Claude API · Pydantic v2 · Rich · Typer · Tenacity
