import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from config import get_output_path, ensure_directories
from utils.logging import get_logger

logger = get_logger(__name__)

def load_association_results() -> pd.DataFrame:
    """
    Load the final association results from data/processed/association_results.csv.
    Expected columns: taxon, coef, pval, qval, direction
    """
    path = get_output_path("data/processed/association_results.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Association results file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} association results from {path}")
    return df

def load_covariate_check_results() -> Dict[str, Any]:
    """
    Load the covariate adjustment check results from results/covariate_delta.json.
    Expected keys: max_delta, threshold_met
    """
    path = get_output_path("results/covariate_delta.json")
    if not os.path.exists(path):
        logger.warning(f"Covariate check results not found: {path}. Skipping inclusion.")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def load_ks_test_results() -> Dict[str, Any]:
    """
    Load the Kolmogorov-Smirnov test results from data/processed/ks_test_results.json.
    Expected keys: statistic, p_value, result
    """
    path = get_output_path("data/processed/ks_test_results.json")
    if not os.path.exists(path):
        logger.warning(f"KS test results not found: {path}. Skipping inclusion.")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def filter_significant_associations(df: pd.DataFrame, q_threshold: float = 0.05) -> pd.DataFrame:
    """
    Filter the association results to include only significant taxa (q < threshold).
    """
    if 'qval' not in df.columns:
        raise ValueError("Association results must contain 'qval' column.")
    
    significant = df[df['qval'] < q_threshold].copy()
    logger.info(f"Found {len(significant)} significant associations (q < {q_threshold})")
    return significant

def generate_report_text(
    significant_df: pd.DataFrame,
    covariate_results: Dict[str, Any],
    ks_results: Dict[str, Any]
) -> str:
    """
    Generate the summary report text content.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("SUMMARY REPORT: Gut Microbiome and Mental Health Association Analysis")
    lines.append("=" * 60)
    lines.append("")

    # Section 1: Significant Associations
    lines.append("1. SIGNIFICANT ASSOCIATIONS (q < 0.05)")
    lines.append("-" * 40)
    
    if significant_df.empty:
        lines.append("No significant associations found at q < 0.05 threshold.")
    else:
        # Sort by q-value
        significant_df = significant_df.sort_values(by='qval')
        lines.append(f"Total significant taxa: {len(significant_df)}")
        lines.append("")
        lines.append("Top Significant Associations:")
        lines.append("-" * 40)
        
        cols = ['taxon', 'coef', 'pval', 'qval', 'direction']
        for col in cols:
            if col not in significant_df.columns:
                significant_df[col] = "N/A"
        
        for _, row in significant_df.iterrows():
            lines.append(f"Taxon: {row['taxon']}")
            lines.append(f"  Coefficient: {row['coef']:.4f}")
            lines.append(f"  Unadjusted p-value: {row['pval']:.4e}")
            lines.append(f"  Adjusted p-value (q): {row['qval']:.4e}")
            lines.append(f"  Direction: {row['direction']}")
            lines.append("")

    # Section 2: Covariate Adjustment Check (SC-005)
    lines.append("")
    lines.append("2. COVARIATE ADJUSTMENT CHECK (SC-005)")
    lines.append("-" * 40)
    
    if covariate_results:
        max_delta = covariate_results.get('max_delta', 'N/A')
        threshold_met = covariate_results.get('threshold_met', False)
        status = "PASS" if threshold_met else "FAIL"
        lines.append(f"Max Delta (|p_adjusted - p_unadjusted|): {max_delta}")
        lines.append(f"Threshold Met (> 0.01): {status}")
    else:
        lines.append("Covariate check results not available.")

    # Section 3: Kolmogorov-Smirnov Test (SC-002)
    lines.append("")
    lines.append("3. KOLMOGOROV-SMIRNOV TEST (SC-002)")
    lines.append("-" * 40)
    
    if ks_results:
        statistic = ks_results.get('statistic', 'N/A')
        p_value = ks_results.get('p_value', 'N/A')
        result = ks_results.get('result', 'N/A')
        lines.append(f"Statistic: {statistic}")
        lines.append(f"P-value: {p_value}")
        lines.append(f"Result: {result}")
    else:
        lines.append("KS test results not available.")

    lines.append("")
    lines.append("=" * 60)
    lines.append("END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)

def write_report(report_text: str, output_path: str) -> None:
    """
    Write the report text to the specified file path.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Report written to {output_path}")

def run_report_generation() -> str:
    """
    Main function to orchestrate report generation.
    Returns the path to the generated report.
    """
    ensure_directories()
    
    # Load data
    logger.info("Loading association results...")
    try:
        assoc_df = load_association_results()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info("Loading covariate check results...")
    covariate_results = load_covariate_check_results()

    logger.info("Loading KS test results...")
    ks_results = load_ks_test_results()

    # Filter significant
    logger.info("Filtering significant associations...")
    significant_df = filter_significant_associations(assoc_df)

    # Generate text
    logger.info("Generating report text...")
    report_text = generate_report_text(significant_df, covariate_results, ks_results)

    # Write output
    output_path = get_output_path("results/summary_report.txt")
    write_report(report_text, output_path)

    return output_path

def main():
    """
    Entry point for the report generation script.
    """
    try:
        output_path = run_report_generation()
        logger.info(f"Report generation completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    main()