import argparse
import logging
import sys
import json
from pathlib import Path
import pandas as pd

from src.utils.io_helpers import load_json_strict, setup_logging

logger = setup_logging("report_generator")

def generate_report():
    """Generate the final report content (text-based for this implementation)."""
    # Load results
    regression_path = Path("data/processed/regression_results.json")
    sensitivity_path = Path("data/processed/sensitivity_metrics.json")
    report_path = Path("reports/final_report.pdf")
    
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not regression_path.exists() or not sensitivity_path.exists():
        logger.warning("Required result files missing. Generating placeholder report text.")
        report_content = "REPORT GENERATION FAILED: Missing input artifacts."
        with open(report_path.with_suffix('.txt'), 'w') as f:
            f.write(report_content)
        return

    try:
        reg_results = load_json_strict(regression_path)
        sens_metrics = load_json_strict(sensitivity_path)
    except Exception as e:
        logger.error(f"Failed to load results: {e}")
        return

    # Construct report text
    report_text = []
    report_text.append("FINAL REPORT: Climate-Smart Agricultural Practices and Yield Stability")
    report_text.append("=" * 60)
    report_text.append("")
    report_text.append("DISCLAIMER: This report presents observational associations. Causal inference is not claimed.")
    report_text.append(f"Bonferroni Correction: Adjusted Alpha = {reg_results.get('adjusted_alpha', 0.05):.4f}")
    report_text.append("")
    report_text.append("1. MODEL SUMMARY")
    report_text.append("-" * 30)
    report_text.append(f"Model Type: {reg_results.get('model_type', 'Unknown')}")
    report_text.append(f"Collinearity Warning: {reg_results.get('collinearity_warning', False)}")
    report_text.append("")
    
    report_text.append("2. SENSITIVITY ANALYSIS")
    report_text.append("-" * 30)
    for model, metrics in sens_metrics.items():
        report_text.append(f"{model}:")
        report_text.append(f"  Max Delta Coefficient: {metrics['max_delta_coefficient']:.4f}")
        report_text.append(f"  Std Coefficient: {metrics['std_coefficient']:.4f}")
    report_text.append("")
    
    report_text.append("3. LIMITATIONS")
    report_text.append("-" * 30)
    report_text.append("- Observational design limits causal claims.")
    report_text.append("- Spatial fuzzing (1km buffer) may introduce measurement error.")
    report_text.append("- Sample size constraints may affect power.")
    report_text.append("")
    report_text.append("END OF REPORT")

    # Write as text file since PDF generation requires heavy deps not guaranteed
    # In a full implementation, this would use reportlab/matplotlib
    with open(report_path.with_suffix('.txt'), 'w') as f:
        f.write("\n".join(report_text))
    
    logger.info(f"Report generated (text version) at {report_path.with_suffix('.txt')}")

def main():
    generate_report()

if __name__ == "__main__":
    main()
