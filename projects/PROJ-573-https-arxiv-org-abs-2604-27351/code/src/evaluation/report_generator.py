"""
Report Generator for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Generates CSV and PDF reports containing statistical analysis results including:
- Paired t-test statistics (t-statistic, p-value)
- Wilcoxon signed-rank test effect size (r) with 95% CI
- Bootstrap confidence intervals (1000 resamples)

FR-007 Compliance: Reports must include all statistical outcomes with effect sizes
as the primary outcome metric.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import logging
from datetime import datetime

import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Break
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.utils.logging import get_logger
from src.evaluation.statistical_tests import (
    paired_ttest,
    wilcoxon_effect_size,
    bootstrap_ci,
    run_full_statistical_analysis
)

logger = get_logger(__name__)


def _ensure_output_dir(output_path: str) -> Path:
    """Ensure the directory for the output file exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def generate_csv_report(
    results: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generate a CSV report containing statistical test results.

    The report includes:
    - task_id
    - condition_a (baseline)
    - condition_b (experimental)
    - t_statistic
    - p_value (t-test)
    - wilcoxon_r (effect size)
    - wilcoxon_p (p-value)
    - bootstrap_mean_diff
    - bootstrap_ci_lower
    - bootstrap_ci_upper
    - timestamp

    Args:
        results: List of dictionaries containing statistical analysis results.
                Each dict should have keys: task_id, condition_a, condition_b,
                and results from run_full_statistical_analysis.
        output_path: Path to write the CSV file.

    Returns:
        The absolute path to the generated CSV file.
    """
    path = _ensure_output_dir(output_path)

    fieldnames = [
        'task_id',
        'condition_a',
        'condition_b',
        't_statistic',
        'p_value_ttest',
        'wilcoxon_r',
        'wilcoxon_p',
        'bootstrap_mean_diff',
        'bootstrap_ci_lower',
        'bootstrap_ci_upper',
        'timestamp'
    ]

    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            row = {
                'task_id': result.get('task_id', 'unknown'),
                'condition_a': result.get('condition_a', 'N/A'),
                'condition_b': result.get('condition_b', 'N/A'),
                't_statistic': result.get('t_statistic', 'N/A'),
                'p_value_ttest': result.get('p_value_ttest', 'N/A'),
                'wilcoxon_r': result.get('wilcoxon_r', 'N/A'),
                'wilcoxon_p': result.get('wilcoxon_p', 'N/A'),
                'bootstrap_mean_diff': result.get('bootstrap_mean_diff', 'N/A'),
                'bootstrap_ci_lower': result.get('bootstrap_ci_lower', 'N/A'),
                'bootstrap_ci_upper': result.get('bootstrap_ci_upper', 'N/A'),
                'timestamp': result.get('timestamp', datetime.now().isoformat())
            }
            writer.writerow(row)

    logger.info(f"CSV report generated: {path}")
    return str(path)


def generate_pdf_report(
    results: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generate a PDF report containing statistical analysis results.

    The report includes:
    - Title and metadata
    - Summary table of all statistical tests
    - Detailed breakdown of t-test, Wilcoxon effect size (PRIMARY), and bootstrap CI

    Args:
        results: List of dictionaries containing statistical analysis results.
        output_path: Path to write the PDF file.

    Returns:
        The absolute path to the generated PDF file.
    """
    path = _ensure_output_dir(output_path)
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )

    # Title
    story.append(Paragraph(
        "Heterogeneous Scientific Foundation Model Benchmark - Statistical Report",
        title_style
    ))
    story.append(Spacer(1, 20))

    # Metadata
    meta_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
    meta_text += f"Total Tasks Analyzed: {len(results)}<br/>"
    meta_text += "Statistical Methods: Paired t-test, Wilcoxon Signed-Rank (Effect Size as Primary), Bootstrap CI (1000 resamples)"
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 20))

    # Prepare table data
    headers = [
        "Task ID",
        "Condition A",
        "Condition B",
        "t-stat",
        "p-val (t)",
        "Effect Size (r)*",
        "p-val (W)",
        "Mean Diff (Boot)",
        "95% CI Lower",
        "95% CI Upper"
    ]

    table_data = [headers]

    for r in results:
        row = [
            str(r.get('task_id', 'N/A')),
            str(r.get('condition_a', 'N/A'))[:15],  # Truncate for fit
            str(r.get('condition_b', 'N/A'))[:15],
            f"{r.get('t_statistic', 'N/A'):.4f}" if isinstance(r.get('t_statistic'), (int, float)) else str(r.get('t_statistic')),
            f"{r.get('p_value_ttest', 'N/A'):.4f}" if isinstance(r.get('p_value_ttest'), (int, float)) else str(r.get('p_value_ttest')),
            f"{r.get('wilcoxon_r', 'N/A'):.4f}" if isinstance(r.get('wilcoxon_r'), (int, float)) else str(r.get('wilcoxon_r')),
            f"{r.get('wilcoxon_p', 'N/A'):.4f}" if isinstance(r.get('wilcoxon_p'), (int, float)) else str(r.get('wilcoxon_p')),
            f"{r.get('bootstrap_mean_diff', 'N/A'):.4f}" if isinstance(r.get('bootstrap_mean_diff'), (int, float)) else str(r.get('bootstrap_mean_diff')),
            f"{r.get('bootstrap_ci_lower', 'N/A'):.4f}" if isinstance(r.get('bootstrap_ci_lower'), (int, float)) else str(r.get('bootstrap_ci_lower')),
            f"{r.get('bootstrap_ci_upper', 'N/A'):.4f}" if isinstance(r.get('bootstrap_ci_upper'), (int, float)) else str(r.get('bootstrap_ci_upper'))
        ]
        table_data.append(row)

    # Create table
    # Adjust column widths to fit letter page (approx 800 points wide)
    col_widths = [1.0*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch]
    t = Table(table_data, colWidths=col_widths)

    # Style the table
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))

    story.append(t)
    story.append(Spacer(1, 12))

    # Legend/Notes
    notes_text = (
        "<b>* Primary Outcome Metric:</b> Wilcoxon Effect Size (r) calculated as Z/√N.<br/>"
        "Effect size interpretation: 0.1 (small), 0.3 (medium), 0.5 (large).<br/>"
        "Bootstrap CI computed with 1000 resamples at 95% confidence level.<br/>"
        "Significance level (α) set to 0.05."
    )
    story.append(Paragraph(notes_text, styles['Normal']))

    # Build PDF
    doc.build(story)
    logger.info(f"PDF report generated: {path}")
    return str(path)


def generate_reports(
    results: List[Dict[str, Any]],
    csv_output_path: str,
    pdf_output_path: str
) -> tuple:
    """
    Generate both CSV and PDF reports from statistical analysis results.

    Args:
        results: List of statistical analysis results.
        csv_output_path: Path for the CSV file.
        pdf_output_path: Path for the PDF file.

    Returns:
        Tuple of (csv_path, pdf_path)
    """
    csv_path = generate_csv_report(results, csv_output_path)
    pdf_path = generate_pdf_report(results, pdf_output_path)
    return csv_path, pdf_path


def main():
    """
    Main entry point for testing the report generator.
    Generates sample reports using mock data to verify functionality.
    """
    # Mock data simulating output from run_full_statistical_analysis
    sample_results = [
        {
            "task_id": "T001",
            "condition_a": "Heterogeneous",
            "condition_b": "Unified",
            "t_statistic": 2.45,
            "p_value_ttest": 0.018,
            "wilcoxon_r": 0.42,
            "wilcoxon_p": 0.012,
            "bootstrap_mean_diff": 0.035,
            "bootstrap_ci_lower": 0.012,
            "bootstrap_ci_upper": 0.058,
            "timestamp": datetime.now().isoformat()
        },
        {
            "task_id": "T002",
            "condition_a": "Heterogeneous",
            "condition_b": "Unified",
            "t_statistic": 1.12,
            "p_value_ttest": 0.265,
            "wilcoxon_r": 0.15,
            "wilcoxon_p": 0.310,
            "bootstrap_mean_diff": 0.008,
            "bootstrap_ci_lower": -0.015,
            "bootstrap_ci_upper": 0.031,
            "timestamp": datetime.now().isoformat()
        },
        {
            "task_id": "T003",
            "condition_a": "Heterogeneous",
            "condition_b": "Unified",
            "t_statistic": 3.89,
            "p_value_ttest": 0.0003,
            "wilcoxon_r": 0.58,
            "wilcoxon_p": 0.0001,
            "bootstrap_mean_diff": 0.062,
            "bootstrap_ci_lower": 0.035,
            "bootstrap_ci_upper": 0.089,
            "timestamp": datetime.now().isoformat()
        }
    ]

    # Define output paths relative to project root
    output_dir = Path("data/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "statistical_results.csv"
    pdf_path = output_dir / "statistical_results.pdf"

    print(f"Generating reports for {len(sample_results)} tasks...")
    csv_final, pdf_final = generate_reports(
        sample_results,
        str(csv_path),
        str(pdf_path)
    )

    print(f"CSV Report: {csv_final}")
    print(f"PDF Report: {pdf_final}")
    print("Report generation complete.")


if __name__ == "__main__":
    main()
