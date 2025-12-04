from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from .extractor import extract_from_dir
from .schema import Invoice
from .validator import validate_invoices


app = typer.Typer(help="Invoice Extraction & Quality Control CLI")
console = Console()


@app.command()
def extract(
    pdf_dir: str = typer.Option(..., help="Folder containing invoice PDFs"),
    output: str = typer.Option("extracted_invoices.json", help="Output JSON file path"),
):
    """Extract structured invoices from PDFs and save to JSON."""
    pdf_path = Path(pdf_dir)
    if not pdf_path.exists():
        typer.echo(f"PDF directory not found: {pdf_dir}")
        raise typer.Exit(code=1)

    invoices = extract_from_dir(pdf_path)
    data = [inv.model_dump() for inv in invoices]

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"[green]Extracted {len(invoices)} invoices[/green] → {out_path}")


@app.command()
def validate(
    input: str = typer.Option(..., help="Input JSON file with extracted invoices"),
    report: str = typer.Option("validation_report.json", help="Validation report output file"),
):
    """Validate invoices from JSON and save QC report."""
    in_path = Path(input)
    if not in_path.exists():
        typer.echo(f"Input file not found: {input}")
        raise typer.Exit(code=1)

    raw = json.loads(in_path.read_text(encoding="utf-8"))
    invoices = [Invoice.model_validate(x) for x in raw]

    result = validate_invoices(invoices)

    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    _print_summary(result["summary"])

    # non-zero exit code if invalid invoices present
    if result["summary"]["invalid_invoices"] > 0:
        raise typer.Exit(code=2)


@app.command("full-run")
def full_run(
    pdf_dir: str = typer.Option(..., help="Folder containing invoice PDFs"),
    report: str = typer.Option("validation_report.json", help="Validation report output file"),
):
    """Extract from PDFs and validate in a single step."""
    invoices = extract_from_dir(pdf_dir)
    result = validate_invoices(invoices)

    report_path = Path(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    _print_summary(result["summary"])

    if result["summary"]["invalid_invoices"] > 0:
        raise typer.Exit(code=2)


def _print_summary(summary: dict):
    console.print("\n[bold]Validation Summary[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value")

    table.add_row("Total invoices", str(summary["total_invoices"]))
    table.add_row("Valid invoices", str(summary["valid_invoices"]))
    table.add_row("Invalid invoices", str(summary["invalid_invoices"]))

    console.print(table)

    if summary["error_counts"]:
        console.print("\n[bold]Top error types[/bold]")
        err_table = Table(show_header=True, header_style="bold red")
        err_table.add_column("Error")
        err_table.add_column("Count")

        for err, count in summary["error_counts"].items():
            err_table.add_row(err, str(count))

        console.print(err_table)


if __name__ == "__main__":
    app()
