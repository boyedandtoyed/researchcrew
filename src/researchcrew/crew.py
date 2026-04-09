from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
from .agents import planner_agent, researcher_agent, writer_agent
from .models import ResearchReport

console = Console()

def run_research(topic: str) -> ResearchReport:
    """Orchestrate the full multi-agent research pipeline."""
    console.print(Panel(f"[bold blue]ResearchCrew[/bold blue] — [white]{topic}[/white]", border_style="blue"))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        # Stage 1: Planning
        t = progress.add_task("[cyan]Planner agent: decomposing topic...", total=None)
        plan = planner_agent(topic)
        progress.update(t, description=f"[green]✓ Plan ready: {len(plan.sub_questions)} sub-questions")
        progress.stop_task(t)

        # Stage 2: Research each sub-question
        findings = []
        context_accumulator = ""
        for i, question in enumerate(plan.sub_questions, 1):
            t2 = progress.add_task(f"[cyan]Researcher [{i}/{len(plan.sub_questions)}]: {question[:50]}...", total=None)
            finding = researcher_agent(topic, question, context=context_accumulator)
            findings.append(finding)
            context_accumulator += f"\n{question}: {'; '.join(finding.key_points[:2])}"
            progress.update(t2, description=f"[green]✓ Finding {i}: {finding.confidence} confidence")
            progress.stop_task(t2)

        # Stage 3: Write report
        t3 = progress.add_task("[cyan]Writer agent: synthesizing report...", total=None)
        report = writer_agent(plan, findings)
        progress.update(t3, description="[green]✓ Report complete")
        progress.stop_task(t3)

    return report

def print_report(report: ResearchReport) -> None:
    console.print(f"\n[bold white]# {report.title}[/bold white]\n")
    console.print(Panel(report.executive_summary, title="Executive Summary", border_style="cyan"))

    for i, finding in enumerate(report.findings, 1):
        console.print(f"\n[bold blue]Finding {i}:[/bold blue] [white]{finding.sub_question}[/white]")
        for point in finding.key_points:
            console.print(f"  [dim]•[/dim] {point}")
        conf_color = {"high": "green", "medium": "yellow", "low": "red"}.get(finding.confidence, "white")
        console.print(f"  [dim]Confidence: [{conf_color}]{finding.confidence}[/{conf_color}][/dim]")

    console.print(f"\n[bold blue]Conclusions:[/bold blue]")
    for c in report.conclusions:
        console.print(f"  [green]→[/green] {c}")

    if report.further_research:
        console.print(f"\n[bold blue]Further Research:[/bold blue]")
        for f in report.further_research:
            console.print(f"  [dim]•[/dim] {f}")

    console.print(f"\n[dim]{report.sources_note}[/dim]")
