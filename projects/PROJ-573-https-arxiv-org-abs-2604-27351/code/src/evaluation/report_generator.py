import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import logging
from datetime import datetime

# Fixed import: use PageBreak instead of non-existent Break
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet


logger = logging.getLogger(__name__)


def generate_csv_report(results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """
    Generate a CSV report from a list of result dictionaries.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of dictionaries where each dict represents a task's results.
    output_path : Union[str, Path]
        Destination path for the CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not results:
        logger.warning("No results provided for CSV report generation.")
        return

    fieldnames = sorted({key for result in results for key in result.keys()})

    with output_path.open(mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    logger.info(f"CSV report written to {output_path}")


def generate_pdf_report(results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """
    Generate a simple PDF report summarizing the benchmark results.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of dictionaries where each dict represents a task's results.
    output_path : Union[str, Path]
        Destination path for the PDF file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph("Benchmark Results Summary", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Timestamp
    timestamp = Paragraph(f"Generated on: {datetime.now().isoformat()}", styles["Normal"])
    elements.append(timestamp)
    elements.append(Spacer(1, 24))

    if not results:
        elements.append(Paragraph("No results to display.", styles["Normal"]))
    else:
        # Table header
        headers = sorted({key for result in results for key in result.keys()})
        data = [headers]

        # Table rows
        for result in results:
            row = [result.get(col, "") for col in headers]
            data.append(row)

        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        elements.append(table)

    # Add a page break at the end for consistency with older implementations
    elements.append(PageBreak())

    doc.build(elements)
    logger.info(f"PDF report written to {output_path}")


def generate_reports(
    results: List[Dict[str, Any]],
    csv_path: Union[str, Path],
    pdf_path: Union[str, Path],
) -> None:
    """
    Convenience wrapper to generate both CSV and PDF reports.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of result dictionaries.
    csv_path : Union[str, Path]
        Destination path for the CSV file.
    pdf_path : Union[str, Path]
        Destination path for the PDF file.
    """
    generate_csv_report(results, csv_path)
    generate_pdf_report(results, pdf_path)


def main() -> None:
    """
    Entry point for manual execution.
    This function demonstrates how the report generator can be invoked
    directly from the command line for debugging or ad‑hoc reporting.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Generate benchmark reports.")
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to output CSV report.",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="Path to output PDF report.",
    )
    args = parser.parse_args()

    # Placeholder: in real usage, results would be loaded from a data source.
    dummy_results = [
        {
            "task_id": "T001",
            "accuracy": 0.87,
            "condition": "heterogeneous",
            "timestamp": datetime.now().isoformat(),
        },
        {
            "task_id": "T002",
            "accuracy": 0.91,
            "condition": "heterogeneous",
            "timestamp": datetime.now().isoformat(),
        },
    ]

    generate_reports(dummy_results, args.csv, args.pdf)


if __name__ == "__main__":
    main()