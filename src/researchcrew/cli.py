import typer
import json
from pathlib import Path
from rich.console import Console
from .crew import run_research, print_report

app = typer.Typer(name="researchcrew", help="Multi-agent deep research using Claude")
console = Console()

@app.command()
def research(
    topic: str = typer.Argument(..., help="Research topic or question"),
    output: Path = typer.Option(None, "--output", "-o", help="Save report as JSON"),
) -> None:
    """Run multi-agent research on a topic."""
    try:
        report = run_research(topic)
        print_report(report)
        if output:
            output.write_text(report.model_dump_json(indent=2))
            console.print(f"\n[green]Report saved to {output}[/green]")
    except Exception as e:
        console.print(f"[red]Research failed: {e}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
