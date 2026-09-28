import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

def load_analysis_cohort():
    """Load analysis cohort."""
    path = Path("data/results/analysis_cohort.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cohort not found at {path}")
    return pd.read_csv(path)

def load_regression_results():
    """Load regression results."""
    path = Path("data/results/regression_results.csv")
    if not path.exists():
        raise FileNotFoundError(f"Results not found at {path}")
    return pd.read_csv(path)

def generate_summary_stats(df):
    """Generate summary statistics."""
    return df.describe()

def format_coefficient(coef):
    """Format coefficient for display."""
    if coef is None:
        return "N/A"
    return f"{coef:.4f}"

def generate_markdown_report(cohort_df, results_df):
    """Generate markdown report."""
    report = "# Regression Summary Report\n\n"
    report += "## Cohort Summary\n"
    report += f"- Sample Size: {len(cohort_df)}\n\n"
    
    report += "## Regression Results\n"
    report += "### Interaction Effects\n"
    report += "| Outcome | Coef | P-value | Adj P-value |\n"
    report += "|---|---|---|---|\n"
    
    for _, row in results_df.iterrows():
        outcome = row.get("outcome", "Unknown")
        coef = row.get("coef_interaction", None)
        pval = row.get("pval_interaction", None)
        adj_pval = row.get("pval_interaction_adj", None)
        
        report += f"| {outcome} | {format_coefficient(coef)} | {format_coefficient(pval)} | {format_coefficient(adj_pval)} |\n"
    
    report += "\n## Interpretation\n"
    report += "The interaction term represents the buffering effect of social support on harassment severity.\n"
    
    return report

def save_report(report):
    """Save report to disk."""
    path = Path("data/results/regression_summary.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report)
    logging.getLogger("results").info(f"Report saved to {path}")

def main():
    """Entry point for results generation."""
    try:
        cohort_df = load_analysis_cohort()
        results_df = load_regression_results()
        report = generate_markdown_report(cohort_df, results_df)
        save_report(report)
        return 0
    except Exception as e:
        logging.getLogger("results").error(f"Results generation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
