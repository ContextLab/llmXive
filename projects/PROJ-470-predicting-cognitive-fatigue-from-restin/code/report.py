"""
Report generation module.
Reads analysis tables and renders markdown reports.
"""
import os
import sys
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import json

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_config(config_path="code/config.yaml"):
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(results_path):
    """Load analysis results JSON."""
    if not os.path.exists(results_path):
        return {}
    with open(results_path, 'r') as f:
        return json.load(f)

def load_sensitivity_table(table_path):
    """Load sensitivity analysis table from CSV."""
    if not os.path.exists(table_path):
        return pd.DataFrame()
    return pd.read_csv(table_path)

def calculate_effect_size(r_value):
    """Calculate effect size (r-squared) from correlation."""
    try:
        return float(r_value) ** 2
    except (TypeError, ValueError):
        return 0.0

def render_markdown_table(df):
    """Render pandas DataFrame to markdown table string."""
    if df.empty:
        return "| No data available |\n|---------------|"
    # Ensure column types are safe for markdown
    return df.to_markdown(index=False)

def generate_report(results, sensitivity_table, output_path="docs/final_report.md"):
    """Generate final markdown report."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report = []
    report.append("# Cognitive Fatigue Analysis Report\n")
    
    # Correlation Analysis Section
    report.append("## Correlation Analysis\n")
    if results:
        if 'r' in results and 'p' in results:
            report.append(f"**Correlation Coefficient (r):** {results['r']:.4f}\n")
            report.append(f"**P-value:** {results['p']:.6f}\n")
            if 'ci_lower' in results and 'ci_upper' in results:
                report.append(f"**95% Confidence Interval:** [{results['ci_lower']:.4f}, {results['ci_upper']:.4f}]\n")
            if 'effect_size' in results:
                report.append(f"**Effect Size (r²):** {results['effect_size']:.4f}\n")
        else:
            report.append(f"Results: {json.dumps(results, indent=2)}\n")
    else:
        report.append("No correlation results available.\n")
    
    # Sensitivity Analysis Section
    report.append("## Sensitivity Analysis\n")
    if not sensitivity_table.empty:
        report.append(render_markdown_table(sensitivity_table))
        report.append("\n")
    else:
        report.append("No sensitivity analysis data available.\n")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

def main():
    logger = setup_logger("report")
    logger.info("Generating report.")
    
    # Load configuration
    config = load_config()
    
    # Define paths
    results_path = Path("data/analysis/results.json")
    sensitivity_path = Path("data/analysis/sensitivity_table.csv")
    output_path = Path("docs/final_report.md")
    
    # Load data
    results = load_analysis_results(results_path)
    sensitivity_df = load_sensitivity_table(sensitivity_path)
    
    # Generate report
    generate_report(results, sensitivity_df, str(output_path))
    
    logger.info(f"Report generated at: {output_path}")

if __name__ == "__main__":
    main()
