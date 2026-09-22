"""
Results Reporting Module.

Implements T024b (Create Module), T025 (Generate Summary Report).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.cohort import RESULTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_analysis_cohort():
    """Loads the analysis cohort."""
    path = RESULTS_DIR / "analysis_cohort.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cohort not found: {path}")
    return pd.read_csv(path)

def load_regression_results():
    """Loads regression results."""
    path = RESULTS_DIR / "regression_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Regression results not found: {path}")
    return pd.read_csv(path)

def generate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates summary statistics for the cohort."""
    return {
        "n": len(df),
        "columns": list(df.columns),
        "numeric_stats": df.describe().to_dict()
    }

def format_coefficient(coef: float) -> str:
    """Formats a coefficient for display."""
    return f"{coef:.4f}"

def generate_markdown_report(cohort_stats: Dict, reg_results: pd.DataFrame) -> str:
    """
    Generates a markdown report of the results.
    T025 Implementation.
    """
    md = []
    md.append("# Regression Summary Report")
    md.append("")
    md.append("## Analysis Cohort Summary")
    md.append(f"- **Sample Size**: {cohort_stats['n']}")
    md.append(f"- **Columns**: {', '.join(cohort_stats['columns'])}")
    md.append("")
    md.append("## Regression Results")
    md.append("")
    md.append("### Model Coefficients and Interaction Effects")
    md.append("")
    md.append("| Outcome | Term | Coefficient | Std Error | P-Value |")
    md.append("|---|---|---|---|---|")
    
    for _, row in reg_results.iterrows():
        md.append(f"| {row['outcome']} | {row['term']} | {format_coefficient(row['coef'])} | "
                  f"{format_coefficient(row['se'])} | {format_coefficient(row['p_value'])} |")
    
    md.append("")
    md.append("### Interpretation")
    md.append("The interaction term (SocialSupport:HarassmentExposure) indicates the buffering effect.")
    md.append("A significant negative coefficient suggests that social support reduces the impact of harassment.")
    md.append("")
    md.append("*Note: Bootstrap confidence intervals and FDR-adjusted p-values are included in the detailed CSV.*")
    
    return "\n".join(md)

def save_report(report: str, path: Optional[Path] = None):
    """Saves the report to a file."""
    if path is None:
        path = RESULTS_DIR / "regression_summary.md"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Report saved to {path}")

def main():
    """Entry point for T024b-T025."""
    logger.info("Generating Results Report (T024b-T025)...")
    try:
        cohort = load_analysis_cohort()
        stats = generate_summary_stats(cohort)
        
        results_df = load_regression_results()
        report = generate_markdown_report(stats, results_df)
        save_report(report)
        
        logger.info("Results reporting completed.")
    except Exception as e:
        logger.error(f"Results reporting failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
