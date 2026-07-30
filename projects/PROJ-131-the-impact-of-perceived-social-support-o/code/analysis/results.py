import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

from logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
COHORT_PATH = PROJECT_ROOT / "data" / "results" / "analysis_cohort.csv"
REGRESSION_RESULTS_PATH = PROJECT_ROOT / "data" / "results" / "regression_results.csv"
SUMMARY_REPORT_PATH = PROJECT_ROOT / "data" / "results" / "regression_summary.md"

def load_analysis_cohort() -> pd.DataFrame:
    """Load the validated analysis cohort from disk."""
    if not COHORT_PATH.exists():
        raise FileNotFoundError(f"Analysis cohort not found at {COHORT_PATH}. "
                                "Ensure T016 has been executed successfully.")
    logger.info(f"Loading analysis cohort from {COHORT_PATH}")
    return pd.read_csv(COHORT_PATH)

def load_regression_results() -> pd.DataFrame:
    """Load the regression results (coefficients, p-values, CIs) from disk."""
    if not REGRESSION_RESULTS_PATH.exists():
        raise FileNotFoundError(f"Regression results not found at {REGRESSION_RESULTS_PATH}. "
                                "Ensure T024 has been executed successfully.")
    logger.info(f"Loading regression results from {REGRESSION_RESULTS_PATH}")
    return pd.read_csv(REGRESSION_RESULTS_PATH)

def generate_summary_stats(cohort: pd.DataFrame, results: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate summary statistics for the report:
    - Cohort size and demographics
    - Model fit summary
    - Key interaction findings
    """
    stats = {
        "cohort_size": len(cohort),
        "demographics": {},
        "models_fitted": len(results),
        "significant_interactions": 0,
        "interaction_details": []
    }

    # Demographics
    if 'age' in cohort.columns:
        stats["demographics"]["mean_age"] = cohort['age'].mean()
        stats["demographics"]["std_age"] = cohort['age'].std()
    if 'gender' in cohort.columns:
        stats["demographics"]["gender_distribution"] = cohort['gender'].value_counts().to_dict()
    if 'education' in cohort.columns:
        stats["demographics"]["education_distribution"] = cohort['education'].value_counts().to_dict()

    # Model findings
    for _, row in results.iterrows():
        outcome = row.get('outcome', 'Unknown')
        interaction_p = row.get('interaction_p_value', 1.0)
        interaction_coef = row.get('interaction_coef', 0.0)
        interaction_ci_low = row.get('interaction_ci_low', 0.0)
        interaction_ci_high = row.get('interaction_ci_high', 0.0)
        fdr_adj_p = row.get('fdr_adj_p_value', 1.0)

        is_significant = fdr_adj_p < 0.05
        if is_significant:
            stats["significant_interactions"] += 1

        stats["interaction_details"].append({
            "outcome": outcome,
            "coefficient": interaction_coef,
            "std_error": row.get('interaction_se', 0.0),
            "p_value": row.get('interaction_p_value', 0.0),
            "fdr_adj_p": fdr_adj_p,
            "ci_low": interaction_ci_low,
            "ci_high": interaction_ci_high,
            "significant": is_significant
        })

    return stats

def format_coefficient(val: float) -> str:
    """Format a float coefficient for display."""
    if pd.isna(val):
        return "N/A"
    return f"{val:.3f}"

def generate_markdown_report(stats: Dict[str, Any]) -> str:
    """Generate the Markdown content for the summary report."""
    lines = []
    lines.append("# Regression Analysis Summary Report")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append(f"This report summarizes the results of the OLS regression analysis examining the")
    lines.append(f"interaction between perceived social support and harassment exposure on mental health outcomes.")
    lines.append(f"Analysis was performed on a single-dataset cohort (Cyberbullying Survey 2021).")
    lines.append("")
    lines.append(f"- **Total Sample Size**: {stats['cohort_size']:,}")
    lines.append(f"- **Models Fitted**: {stats['models_fitted']}")
    lines.append(f"- **Significant Interaction Effects (FDR < 0.05)**: {stats['significant_interactions']}")
    lines.append("")

    # Demographics
    lines.append("## 2. Cohort Characteristics")
    lines.append("")
    if stats["demographics"]:
        lines.append("| Metric | Value |")
        lines.append("| :--- | :--- |")
        if "mean_age" in stats["demographics"]:
            lines.append(f"| Mean Age | {stats['demographics']['mean_age']:.2f} (SD: {stats['demographics']['std_age']:.2f}) |")
        if "gender_distribution" in stats["demographics"]:
            gender_str = ", ".join([f"{k}: {v}" for k, v in stats["demographics"]["gender_distribution"].items()])
            lines.append(f"| Gender Distribution | {gender_str} |")
        if "education_distribution" in stats["demographics"]:
            edu_str = ", ".join([f"{k}: {v}" for k, v in stats["demographics"]["education_distribution"].items()])
            lines.append(f"| Education Distribution | {edu_str} |")
    else:
        lines.append("*Demographic data not available in cohort.*")
    lines.append("")

    # Key Findings
    lines.append("## 3. Key Findings: Interaction Effects")
    lines.append("")
    lines.append("The table below presents the interaction coefficients (Social Support × Harassment Exposure) for each outcome.")
    lines.append("Statistical significance is determined after Benjamini-Hochberg FDR correction (α = 0.05).")
    lines.append("")
    lines.append("| Outcome | Coefficient | SE | 95% CI (BCa) | Raw p-value | FDR Adj. p-value | Significant? |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for detail in stats["interaction_details"]:
        sig_str = "Yes" if detail["significant"] else "No"
        ci_str = f"[{format_coefficient(detail['ci_low'])}, {format_coefficient(detail['ci_high'])}]"
        lines.append(
            f"| {detail['outcome']} | {format_coefficient(detail['coefficient'])} | "
            f"{format_coefficient(detail['std_error'])} | {ci_str} | "
            f"{detail['p_value']:.4f} | {detail['fdr_adj_p']:.4f} | {sig_str} |"
        )
    lines.append("")

    # Interpretation
    lines.append("## 4. Interpretation")
    lines.append("")
    if stats["significant_interactions"] > 0:
        lines.append(f"**Evidence of Buffering Effect Found:**")
        lines.append("")
        lines.append(f"The analysis identified {stats['significant_interactions']} outcome(s) where the interaction between")
        lines.append("social support and harassment exposure was statistically significant after correction.")
        lines.append("A negative interaction coefficient suggests that higher social support attenuates the negative impact")
        lines.append("of harassment on mental health (buffering effect).")
    else:
        lines.append("**No Significant Buffering Effect Detected:**")
        lines.append("")
        lines.append("No interaction effects remained statistically significant after FDR correction.")
        lines.append("This suggests that, in this specific dataset, perceived social support did not significantly")
        lines.append("moderate the relationship between harassment exposure and the measured mental health outcomes,")
        lines.append("or the study was underpowered to detect small interaction effects.")
    lines.append("")
    lines.append("## 5. Methodological Notes")
    lines.append("")
    lines.append("- **Data Source**: Cyberbullying Survey 2021 (Single-dataset approach).")
    lines.append("- **Imputation**: Multiple Imputation by Chained Equations (MICE) used for missing data.")
    lines.append("- **Inference**: Bias-Corrected Accelerated (BCa) Bootstrap CIs (1,000 resamples) and HC3 standard errors.")
    lines.append("- **Multiple Testing**: Benjamini-Hochberg FDR correction applied across outcomes.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated automatically by the llmXive pipeline.*")
    lines.append(f"*Timestamp: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)

def save_report(content: str, path: Path) -> None:
    """Save the generated markdown report to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Regression summary report saved to {path}")

def main() -> None:
    """
    Main entry point for T025.
    Reads analysis_cohort.csv and regression_results.csv,
    generates a summary report, and saves it to data/results/regression_summary.md.
    """
    try:
        # 1. Load Data
        cohort = load_analysis_cohort()
        results = load_regression_results()

        # 2. Generate Statistics
        stats = generate_summary_stats(cohort, results)

        # 3. Generate Report
        report_content = generate_markdown_report(stats)

        # 4. Save Report
        save_report(report_content, SUMMARY_REPORT_PATH)

        logger.info("Task T025 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to generate summary report: {e}")
        raise

if __name__ == "__main__":
    main()