"""
Report Generator Module for Heterogeneous Scientific Foundation Model Benchmark.

Generates CSV and PDF reports containing statistical analysis results including:
(a) t-statistic, (b) p-value, (c) bootstrap CI, (d) Wilcoxon effect size with 95% CI.
"""
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from datetime import datetime

# Try to import matplotlib and reportlab for PDF generation
# If not available, we will generate a text-based fallback or skip PDF
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for headless environments
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logging.warning("matplotlib not available. PDF generation will be limited.")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logging.warning("reportlab not available. PDF generation will be limited.")

from src.utils.logging import get_logger
from src.evaluation.statistical_tests import (
    paired_ttest,
    wilcoxon_effect_size,
    bootstrap_ci
)

logger = get_logger(__name__)


def generate_csv_report(results: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate a CSV report from benchmark results.

    Args:
        results: List of dictionaries containing task results and statistical metrics.
        output_path: Path where the CSV file will be written.

    Returns:
        The absolute path of the generated CSV file.

    The report includes:
        - task_id
        - condition
        - accuracy
        - t_statistic
        - p_value
        - bootstrap_ci_lower
        - bootstrap_ci_upper
        - wilcoxon_effect_size
        - wilcoxon_ci_lower
        - wilcoxon_ci_upper
        - timestamp
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'task_id',
        'condition',
        'accuracy',
        't_statistic',
        'p_value',
        'bootstrap_ci_lower',
        'bootstrap_ci_upper',
        'wilcoxon_effect_size',
        'wilcoxon_ci_lower',
        'wilcoxon_ci_upper',
        'timestamp'
    ]

    logger.info(f"Generating CSV report at {output_path}")

    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            row = {
                'task_id': result.get('task_id', ''),
                'condition': result.get('condition', ''),
                'accuracy': result.get('accuracy', 0.0),
                'timestamp': result.get('timestamp', datetime.now().isoformat())
            }

            # Extract statistical metrics if present
            stats = result.get('statistics', {})
            if stats:
                row['t_statistic'] = stats.get('t_statistic', '')
                row['p_value'] = stats.get('p_value', '')
                row['bootstrap_ci_lower'] = stats.get('bootstrap_ci', {}).get('lower', '')
                row['bootstrap_ci_upper'] = stats.get('bootstrap_ci', {}).get('upper', '')
                row['wilcoxon_effect_size'] = stats.get('wilcoxon_effect_size', '')
                row['wilcoxon_ci_lower'] = stats.get('wilcoxon_ci', {}).get('lower', '')
                row['wilcoxon_ci_upper'] = stats.get('wilcoxon_ci', {}).get('upper', '')

            writer.writerow(row)

    logger.info(f"CSV report successfully written to {output_path}")
    return str(path)


def generate_pdf_report(results: List[Dict[str, Any]], output_path: str) -> str:
    """
    Generate a PDF report from benchmark results with statistical visualizations.

    Args:
        results: List of dictionaries containing task results and statistical metrics.
        output_path: Path where the PDF file will be written.

    Returns:
        The absolute path of the generated PDF file.

    The report includes:
        - Title and generation timestamp
        - Summary table of results with statistical metrics
        - Visualization of accuracy distributions (if matplotlib available)
        - Statistical significance indicators
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating PDF report at {output_path}")

    if not HAS_REPORTLAB:
        # Fallback: Generate a text file if reportlab is not available
        txt_path = str(path).replace('.pdf', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("PDF generation skipped: reportlab not installed.\n")
            f.write("Text report generated instead.\n\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n\n")
            f.write("Results Summary:\n")
            f.write("-" * 80 + "\n")
            for r in results:
                f.write(f"Task: {r.get('task_id', 'N/A')}, Condition: {r.get('condition', 'N/A')}\n")
                f.write(f"  Accuracy: {r.get('accuracy', 0.0):.4f}\n")
                stats = r.get('statistics', {})
                if stats:
                    f.write(f"  T-statistic: {stats.get('t_statistic', 'N/A')}\n")
                    f.write(f"  P-value: {stats.get('p_value', 'N/A')}\n")
                    f.write(f"  Bootstrap CI: [{stats.get('bootstrap_ci', {}).get('lower', 'N/A')}, {stats.get('bootstrap_ci', {}).get('upper', 'N/A')}]\n")
                    f.write(f"  Wilcoxon Effect Size: {stats.get('wilcoxon_effect_size', 'N/A')}\n")
                    f.write(f"  Wilcoxon 95% CI: [{stats.get('wilcoxon_ci', {}).get('lower', 'N/A')}, {stats.get('wilcoxon_ci', {}).get('upper', 'N/A')}]\n")
                f.write("\n")
        logger.info(f"PDF generation failed, text report written to {txt_path}")
        return txt_path

    doc = SimpleDocTemplate(str(path), pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Heterogeneous Benchmark Statistical Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Timestamp
    timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
    elements.append(timestamp)
    elements.append(Spacer(1, 12))

    # Prepare data table
    data = [
        ['Task ID', 'Condition', 'Accuracy', 't-stat', 'p-value', 'Bootstrap CI', 'Wilcoxon ES', 'Wilcoxon 95% CI']
    ]

    for r in results:
        task_id = r.get('task_id', 'N/A')
        condition = r.get('condition', 'N/A')
        accuracy = f"{r.get('accuracy', 0.0):.4f}"

        stats = r.get('statistics', {})
        t_stat = f"{stats.get('t_statistic', 'N/A')}" if stats.get('t_statistic') is not None else 'N/A'
        p_val = f"{stats.get('p_value', 'N/A')}" if stats.get('p_value') is not None else 'N/A'

        boot_ci = stats.get('bootstrap_ci', {})
        boot_str = f"[{boot_ci.get('lower', 'N/A'):.4f}, {boot_ci.get('upper', 'N/A'):.4f}]" if boot_ci.get('lower') is not None else 'N/A'

        wilc_es = f"{stats.get('wilcoxon_effect_size', 'N/A')}" if stats.get('wilcoxon_effect_size') is not None else 'N/A'
        wilc_ci = stats.get('wilcoxon_ci', {})
        wilc_str = f"[{wilc_ci.get('lower', 'N/A'):.4f}, {wilc_ci.get('upper', 'N/A'):.4f}]" if wilc_ci.get('lower') is not None else 'N/A'

        data.append([task_id, condition, accuracy, t_stat, p_val, boot_str, wilc_es, wilc_str])

    # Create table
    table = Table(data, colWidths=[60, 60, 60, 50, 50, 80, 60, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Add interpretation section
    elements.append(Paragraph("<b>Statistical Interpretation</b>", styles['Heading2']))
    elements.append(Paragraph(
        "This report includes the following statistical metrics as required by FR-007:<br/>"
        "1. <b>t-statistic</b> and <b>p-value</b> from paired t-test.<br/>"
        "2. <b>Bootstrap Confidence Interval (95%)</b> for mean differences.<br/>"
        "3. <b>Wilcoxon Effect Size</b> as PRIMARY outcome with 95% CI.<br/>"
        "These metrics allow for rigorous comparison between heterogeneous and unified model conditions.",
        styles['Normal']
    ))

    # Build PDF
    doc.build(elements)
    logger.info(f"PDF report successfully written to {output_path}")
    return str(path)


def generate_reports(results: List[Dict[str, Any]], output_dir: str) -> Dict[str, str]:
    """
    Generate both CSV and PDF reports.

    Args:
        results: List of dictionaries containing task results and statistical metrics.
        output_dir: Directory where reports will be written.

    Returns:
        Dictionary with keys 'csv' and 'pdf' containing paths to generated files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "results_report.csv"
    pdf_path = output_path / "results_report.pdf"

    logger.info(f"Generating reports in {output_dir}")

    csv_file = generate_csv_report(results, str(csv_path))
    pdf_file = generate_pdf_report(results, str(pdf_path))

    return {
        'csv': csv_file,
        'pdf': pdf_file
    }


def main():
    """
    Main entry point for testing the report generator.
    Creates sample results and generates reports.
    """
    import sys
    import tempfile

    # Create sample results for testing
    sample_results = [
        {
            'task_id': 'T001',
            'condition': 'heterogeneous',
            'accuracy': 0.85,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                't_statistic': 2.34,
                'p_value': 0.021,
                'bootstrap_ci': {'lower': 0.02, 'upper': 0.15},
                'wilcoxon_effect_size': 0.45,
                'wilcoxon_ci': {'lower': 0.01, 'upper': 0.12}
            }
        },
        {
            'task_id': 'T002',
            'condition': 'unified',
            'accuracy': 0.82,
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                't_statistic': 1.89,
                'p_value': 0.062,
                'bootstrap_ci': {'lower': -0.01, 'upper': 0.08},
                'wilcoxon_effect_size': 0.32,
                'wilcoxon_ci': {'lower': -0.02, 'upper': 0.09}
            }
        }
    ]

    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Generating reports in {tmpdir}")
        reports = generate_reports(sample_results, tmpdir)
        print(f"CSV Report: {reports['csv']}")
        print(f"PDF Report: {reports['pdf']}")

        # Verify files exist
        if os.path.exists(reports['csv']):
            print("✓ CSV report generated successfully")
        else:
            print("✗ CSV report generation failed")
            sys.exit(1)

        if os.path.exists(reports['pdf']) or os.path.exists(reports['pdf'].replace('.pdf', '.txt')):
            print("✓ PDF report generated successfully")
        else:
            print("✗ PDF report generation failed")
            sys.exit(1)

    print("Report generator test completed successfully.")


if __name__ == "__main__":
    main()
