"""
Report Generator

Assembles plots and tables into a PDF report.
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from code.utils.logging_config import setup_logging, get_logger

def generate_report():
    """
    Generate final PDF report.
    """
    logger = get_logger("report")
    logger.info("Generating Report")

    output_path = project_root / "outputs" / "final_report.pdf"
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Network Centrality and Cognitive Decline Analysis")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 80, "This report summarizes the findings from the analysis pipeline.")

    # Add QC summary
    qc_summary_path = project_root / "data" / "analysis" / "qc_summary.json"
    if qc_summary_path.exists():
        with open(qc_summary_path, "r") as f:
            qc_data = json.load(f)
        c.drawString(100, height - 110, f"Usable Participants: {qc_data.get('usable_count', 'N/A')}")

    c.save()
    logger.info(f"Report saved to {output_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Generate Report")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    log_path = project_root / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path=log_path, level=args.log_level)

    return generate_report()

if __name__ == "__main__":
    sys.exit(main())
