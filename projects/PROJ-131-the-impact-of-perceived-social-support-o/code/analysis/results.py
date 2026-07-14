"""
results.py - Generate regression summary report.

Reads the validated synthetic cohort and regression results to produce
a human-readable Markdown summary report.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
COHORT_FILE = RESULTS_DIR / "synthetic_cohort.csv"
REGRESSION_RESULTS_FILE = RESULTS_DIR / "regression_results.csv"
SUMMARY_OUTPUT_FILE = RESULTS_DIR / "regression_summary.md"

def load_synthetic_cohort() -> Optional[pd.DataFrame]:
    """Load the synthetic cohort from disk."""
    if not COHORT_FILE.exists():
        logger.error(f"Cohort file not found: {COHORT_FILE}")
        return None
    try:
        df = pd.read_csv(COHORT_FILE)
        logger.info(f"Loaded synthetic cohort with {len(df)} rows and {len(df.columns)} columns.")
        return df
    except Exception as e:
        logger.error(f"Failed to load synthetic cohort: {e}")
        return None

def load_regression_results() -> Optional[pd.DataFrame]:
    """Load the regression results from disk."""
    if not REGRESSION_RESULTS_FILE.exists():
        logger.error(f"Regression results file not found: {REGRESSION_RESULTS_FILE}")
        return None
    try:
        df = pd.read_csv(REGRESSION_RESULTS_FILE)
        logger.info(f"Loaded regression results with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load regression results: {e}")
        return None

def generate_summary_stats(cohort: pd.DataFrame) -> Dict[str, Any]:
    """Generate basic summary statistics for the cohort."""
    numeric_cols = cohort.select_dtypes(include=[np.number]).columns
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "mean": float(cohort[col].mean()),
            "std": float(cohort[col].std()),
            "min": float(cohort[col].min()),
            "max": float(cohort[col].max()),
            "count": int(cohort[col].count())
        }
    return stats

def format_coefficient(row: pd.Series) -> str:
    """Format a single regression coefficient row for Markdown."""
    outcome = row.get('outcome', 'Unknown')
    predictor = row.get('predictor', 'Unknown')
    coef = row.get('coef', 0.0)
    std_err = row.get('std_err', 0.0)
    p_val = row.get('p_value', 1.0)
    p_adj = row.get('p_adj', 1.0)
    ci_lower = row.get('ci_lower', 0.0)
    ci_upper = row.get('ci_upper', 0.0)
    
    sig_marker = ""
    if p_adj < 0.001:
        sig_marker = "***"
    elif p_adj < 0.01:
        sig_marker = "**"
    elif p_adj < 0.05:
        sig_marker = "*"
    
    return (
        f"| {outcome} | {predictor} | {coef:.4f} {sig_marker} | "
        f"{std_err:.4f} | {p_val:.4f} | {p_adj:.4f} | "
        f"[{ci_lower:.4f}, {ci_upper:.4f}] |"
    )

def generate_markdown_report(cohort: pd.DataFrame, results: pd.DataFrame) -> str:
    """Generate the full Markdown summary report."""
    summary_stats = generate_summary_stats(cohort)
    
    md_lines = [
        "# Regression Analysis Summary: Social Support & Resilience",
        "",
        "## 1. Dataset Overview",
        "",
        f"- **Total Observations**: {len(cohort)}",
        f"- **Variables Analyzed**: {len(cohort.columns)}",
        "",
        "### Descriptive Statistics (Numeric Variables)",
        "",
        "| Variable | Mean | Std Dev | Min | Max | Count |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    
    for var, stats in summary_stats.items():
        md_lines.append(
            f"| {var} | {stats['mean']:.2f} | {stats['std']:.2f} | "
            f"{stats['min']:.2f} | {stats['max']:.2f} | {stats['count']} |"
        )
    
    md_lines.extend([
        "",
        "## 2. Model Results",
        "",
        "This table presents the OLS regression coefficients for the interaction between "
        "Perceived Social Support and Harassment Exposure on mental health outcomes "
        "(Depression, Anxiety, PTSD).",
        "",
        "### Coefficients with Bias-Corrected Bootstrap CIs and FDR-Adjusted P-values",
        "",
        "| Outcome | Predictor | Coefficient | Std Error | P-value | P-adj (FDR) | 95% CI (BCa) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])
    
    if results is not None and not results.empty:
        for _, row in results.iterrows():
            md_lines.append(format_coefficient(row))
    else:
        md_lines.append("| *No results available* | *No results available* | ... |")
    
    md_lines.extend([
        "",
        "### Interpretation Notes",
        "",
        "- **Significance Levels**: * p < 0.05, ** p < 0.01, *** p < 0.001 (FDR-adjusted)",
        "- **Interaction Term**: The coefficient for `SocialSupport:HarassmentExposure` indicates "
          "whether the effect of harassment on the outcome varies by level of social support.",
        "- **Confidence Intervals**: 95% Bias-Corrected and Accelerated (BCa) Bootstrap CIs based on 1,000 resamples.",
        "",
        "## 3. Methodological Context",
        "",
        "- **Data Source**: Synthetic cohort constructed via propensity score matching/weighting.",
        "- **Model**: OLS with Heteroskedasticity-Consistent (HC3) standard errors.",
        "- **Missing Data**: Handled via MICE imputation (m=5) prior to analysis.",
        "- **Multiple Testing**: Benjamini-Hochberg FDR correction applied across outcomes.",
        "",
        "---",
        f"*Report generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    ])
    
    return "\n".join(md_lines)

def save_report(content: str, output_path: Path) -> bool:
    """Save the Markdown report to disk."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Report saved successfully to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return False

def main():
    """Main entry point for generating the regression summary report."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting regression summary report generation.")
    
    # Load data
    cohort = load_synthetic_cohort()
    if cohort is None:
        logger.error("Cannot proceed: Synthetic cohort not found.")
        return 1
        
    results = load_regression_results()
    if results is None:
        logger.error("Cannot proceed: Regression results not found.")
        return 1
    
    # Generate report
    report_content = generate_markdown_report(cohort, results)
    
    # Save report
    if not save_report(report_content, SUMMARY_OUTPUT_FILE):
        logger.error("Failed to save the report.")
        return 1
        
    logger.info("Report generation completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())