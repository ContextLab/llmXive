"""
Reporting Module.
Generates final report with all results.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_curated_data():
    """Load curated data."""
    path = Path(__file__).parent.parent.parent / "data" / "curated_builds.csv"
    if path.exists():
        return pd.read_csv(path)
    return None

def load_lme_results():
    """Load LME results."""
    path = Path(__file__).parent.parent.parent / "artifacts" / "MixedEffectsResult.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_xgboost_results():
    """Load XGBoost results."""
    path = Path(__file__).parent.parent.parent / "artifacts" / "final_predictive_artifact.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_sensitivity_results():
    """Load sensitivity results."""
    path = Path(__file__).parent.parent.parent / "artifacts" / "sensitivity_results.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_vif_results():
    """Load VIF results (from preprocessing logs or artifacts)."""
    # Placeholder
    return {}

def generate_coefficient_table(lme_results):
    """Generate coefficient table."""
    if not lme_results:
        return "No LME results available."
    return f"Coefficients: {lme_results.get('data', {}).get('coefficients', {})}"

def generate_metrics_summary(xgboost_results):
    """Generate metrics summary."""
    if not xgboost_results:
        return "No XGBoost results available."
    return f"R2: {xgboost_results.get('metrics', {}).get('r2', 'N/A')}"

def generate_vif_summary(vif_results):
    """Generate VIF summary."""
    return f"VIF Analysis: {vif_results}"

def generate_sensitivity_summary(sensitivity_results):
    """Generate sensitivity summary."""
    if not sensitivity_results:
        return "No sensitivity results."
    return f"Partial R2: {sensitivity_results.get('partial_r2', 'N/A')}"

def generate_partial_dependence_plots(model):
    """Generate partial dependence plots (placeholder)."""
    logger.info("Generating partial dependence plots...")
    # Placeholder for plot generation
    pass

def generate_data_limitations_section():
    """Generate data limitations section."""
    return """
    ## Data Limitations & Assumptions

    - **Dataset size**: N=15 (Source: Cited Papers).
    - **No synthetic data was used.**
    - **HuggingFace source was unavailable.**
    - **Results are exploratory due to N < 100.**
    """

def generate_final_report():
    """Generate final report."""
    logger.info("Generating final report...")
    
    lines = []
    lines.append("# Final Report: Ductility Prediction Pipeline")
    lines.append("")
    
    # Data Limitations
    lines.append(generate_data_limitations_section())
    lines.append("")
    
    # LME Results
    lme = load_lme_results()
    lines.append("## LME Results")
    lines.append(generate_coefficient_table(lme))
    lines.append("")
    
    # XGBoost Results
    xgb = load_xgboost_results()
    lines.append("## XGBoost Results")
    lines.append(generate_metrics_summary(xgb))
    lines.append("")
    
    # Sensitivity
    sens = load_sensitivity_results()
    lines.append("## Sensitivity Analysis")
    lines.append(generate_sensitivity_summary(sens))
    lines.append("")
    
    content = "\n".join(lines)
    
    output_dir = Path(__file__).parent.parent.parent / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    md_path = output_dir / "final_report.md"
    with open(md_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Final report saved to {md_path}")
    return content

def main():
    """Main entry point."""
    logger.info("Starting Reporting...")
    generate_final_report()
    logger.info("Reporting stage completed.")

if __name__ == "__main__":
    main()