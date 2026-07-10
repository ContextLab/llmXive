import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime

# Importing from analysis module as per API surface
# Note: run_meta_analysis and run_sensitivity_analysis are expected to exist
# in analysis.py to provide the data for this report.
from analysis import run_meta_analysis, run_sensitivity_analysis

logger = logging.getLogger(__name__)

# Paths relative to project root
DATA_RESULTS_DIR = Path("data/results")
SUMMARY_REPORT_PATH = DATA_RESULTS_DIR / "summary_report.txt"

def load_correlation_results() -> Optional[pd.DataFrame]:
    """Load the correlation results from the analysis phase."""
    path = DATA_RESULTS_DIR / "correlation_results.csv"
    if not path.exists():
        logger.warning(f"Correlation results file not found at {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def load_meta_analysis_results() -> Optional[pd.DataFrame]:
    """Load the meta-analysis results from the analysis phase."""
    path = DATA_RESULTS_DIR / "meta_analysis_results.csv"
    if not path.exists():
        logger.warning(f"Meta-analysis results file not found at {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load meta-analysis results: {e}")
        return None

def load_sensitivity_analysis() -> Optional[pd.DataFrame]:
    """Load the sensitivity analysis results from the analysis phase."""
    path = DATA_RESULTS_DIR / "sensitivity_analysis.csv"
    if not path.exists():
        logger.warning(f"Sensitivity analysis file not found at {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load sensitivity analysis: {e}")
        return None

def classify_correlation(r_value: float) -> str:
    """Classify the correlation strength based on |r|."""
    abs_r = abs(r_value)
    if abs_r >= 0.7:
        return "strong"
    elif abs_r >= 0.3:
        return "moderate"
    elif abs_r >= 0.1:
        return "weak"
    else:
        return "negligible"

def generate_summary_report(
    correlation_df: Optional[pd.DataFrame],
    meta_df: Optional[pd.DataFrame],
    sensitivity_df: Optional[pd.DataFrame]
) -> str:
    """
    Generate the summary report text including:
    1. Per-repo and aggregate correlation results.
    2. Meta-analysis outcome.
    3. Sensitivity analysis table.
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"## Research Pipeline Summary Report")
    lines.append(f"Generated: {timestamp}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Correlation Results
    lines.append("## 1. Correlation Analysis Results")
    lines.append("")
    if correlation_df is not None and not correlation_df.empty:
        lines.append("### Per-Repository Results")
        # Format for readability
        for _, row in correlation_df.iterrows():
            repo_id = row.get('repo_id', 'Unknown')
            r_val = row.get('r', 0.0)
            p_val = row.get('p', 1.0)
            classification = classify_correlation(r_val)
            lines.append(f"- **{repo_id}**: r={r_val:.4f}, p={p_val:.4f} ({classification})")
        
        # Aggregate
        if 'r' in correlation_df.columns:
            mean_r = correlation_df['r'].mean()
            lines.append("")
            lines.append(f"**Aggregate Mean r**: {mean_r:.4f}")
    else:
        lines.append("*No correlation results available.*")
    lines.append("")

    # Section 2: Meta-Analysis Outcome
    lines.append("## 2. Meta-Analysis Outcome")
    lines.append("")
    if meta_df is not None and not meta_df.empty:
        # Summarize the meta-analysis
        # Assuming columns: 'method', 'combined_r', 'combined_p', 'ci_lower', 'ci_upper'
        # or similar structure from analysis.py
        combined_r = meta_df['combined_r'].iloc[0] if 'combined_r' in meta_df.columns else "N/A"
        combined_p = meta_df['combined_p'].iloc[0] if 'combined_p' in meta_df.columns else "N/A"
        
        lines.append(f"**Combined Effect Size (r)**: {combined_r}")
        lines.append(f"**P-value**: {combined_p}")
        
        if 'ci_lower' in meta_df.columns and 'ci_upper' in meta_df.columns:
            ci_lower = meta_df['ci_lower'].iloc[0]
            ci_upper = meta_df['ci_upper'].iloc[0]
            lines.append(f"**95% Confidence Interval**: [{ci_lower:.4f}, {ci_upper:.4f}]")
        
        lines.append("")
        lines.append("### Meta-Analysis Details")
        lines.append("```")
        lines.append(meta_df.to_string(index=False))
        lines.append("```")
    else:
        lines.append("*No meta-analysis results available.*")
    lines.append("")

    # Section 3: Sensitivity Analysis
    lines.append("## 3. Sensitivity Analysis (LOC Thresholds)")
    lines.append("")
    if sensitivity_df is not None and not sensitivity_df.empty:
        lines.append("The model was re-run with `avg_loc` thresholds of 5, 10, and 20.")
        lines.append("")
        lines.append("### Results by Threshold")
        lines.append("| Threshold | Mean r | Std Dev r | N |")
        lines.append("| :--- | :--- | :--- | :--- |")
        
        # Group by threshold if possible, or just list rows
        # Assuming columns: 'threshold', 'r', 'p', 'n'
        if 'threshold' in sensitivity_df.columns:
            for _, row in sensitivity_df.iterrows():
                t = row['threshold']
                r = row.get('r', 0)
                std = row.get('std_r', 0) # Fallback if column name differs
                n = row.get('n', 0)
                lines.append(f"| {t} | {r:.4f} | {std:.4f} | {n} |")
        else:
            # Fallback if structure is different
            lines.append(sensitivity_df.to_markdown(index=False))
        
        lines.append("")
    else:
        lines.append("*No sensitivity analysis results available.*")
    
    lines.append("")
    lines.append("---")
    lines.append("*End of Report*")

    return "\n".join(lines)

def save_summary_report(content: str, path: Path) -> None:
    """Save the generated report content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Summary report saved to {path}")

def run_reporting() -> None:
    """
    Orchestrates the loading of analysis results and generation of the summary report.
    This function fulfills T029 by including Meta-analysis and Sensitivity Analysis.
    """
    logger.info("Starting reporting phase (T029)")
    
    # Load data
    correlation_df = load_correlation_results()
    meta_df = load_meta_analysis_results()
    sensitivity_df = load_sensitivity_analysis()
    
    # Generate report
    report_content = generate_summary_report(correlation_df, meta_df, sensitivity_df)
    
    # Save report
    save_summary_report(report_content, SUMMARY_REPORT_PATH)
    
    logger.info("Reporting phase completed successfully.")

def main():
    """Entry point for the reporting script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_reporting()

if __name__ == "__main__":
    main()