import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union

# ReportLab imports – use PageBreak instead of the non‑existent Break class
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)

logger = logging.getLogger(__name__)


def generate_csv_report(
    results: List[Dict[str, Any]], output_path: Union[str, Path]
) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Parameters
    ----------
    results: List[Dict[str, Any]]
        Each dictionary represents a row; keys are column names.
    output_path: Union[str, Path]
        Destination CSV file.  Parent directories are created automatically.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine a stable column order – alphabetical for reproducibility
    fieldnames = sorted({k for row in results for k in row.keys()})

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    logger.info("CSV report written to %s", output_path)


def generate_pdf_report(
    results: List[Dict[str, Any]], output_path: Union[str, Path]
) -> None:
    """
    Create a simple PDF report summarising the benchmark results.

    Parameters
    ----------
    results: List[Dict[str, Any]]
        List of result dictionaries.
    output_path: Union[str, Path]
        Destination PDF file.  Parent directories are created automatically.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Benchmark Results", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    if not results:
        elements.append(Paragraph("No results available.", styles["Normal"]))
    else:
        # Build a table: header row + data rows
        headers = sorted({k for row in results for k in row.keys()})
        data = [headers]  # header row
        for row in results:
            data.append([row.get(col, "") for col in headers])

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        elements.append(table)

    # Finish the document
    doc.build(elements)
    logger.info("PDF report written to %s", output_path)


def generate_reports(
    results: List[Dict[str, Any]],
    csv_path: Union[str, Path],
    pdf_path: Union[str, Path],
) -> None:
    """
    Convenience wrapper that generates both CSV and PDF reports.
    """
    generate_csv_report(results, csv_path)
    generate_pdf_report(results, pdf_path)


def main() -> None:
    """
    CLI entry point – reads a JSON file containing a list of result dicts
    and writes the CSV and PDF reports.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Generate benchmark CSV and PDF reports from a JSON results file"
    )
    parser.add_argument(
        "results_json",
        type=str,
        help="Path to a JSON file containing a list of result dictionaries",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="results.csv",
        help="Destination CSV file (default: results.csv)",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default="summary.pdf",
        help="Destination PDF file (default: summary.pdf)",
    )
    args = parser.parse_args()

    with open(args.results_json, "r", encoding="utf-8") as f:
        results = json.load(f)

    generate_reports(results, args.csv, args.pdf)


if __name__ == "__main__":
    main()