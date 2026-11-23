import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import kstest, uniform
from config import get_output_path

logger = logging.getLogger(__name__)

def load_association_results(filepath: str) -> pd.DataFrame:
    """
    Load the association results CSV containing unadjusted p-values.
    Expected columns: feature, pval_raw (or similar), pval_adj, etc.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Association results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df

def check_significant_taxa(df: pd.DataFrame, q_threshold: float = 0.05) -> bool:
    """
    Check if there are any significant taxa (q-value < threshold).
    Looks for 'pval_adj' or 'qval' column.
    """
    # Try common column names for adjusted p-values
    adj_col = None
    for col in ['pval_adj', 'qval', 'adj_pval', 'q_value']:
        if col in df.columns:
            adj_col = col
            break
    
    if adj_col is None:
        logger.warning("No adjusted p-value column found. Assuming no significant taxa found.")
        return False
    
    significant = df[df[adj_col] < q_threshold]
    has_significant = len(significant) > 0
    logger.info(f"Found {len(significant)} significant taxa with q < {q_threshold}")
    return has_significant

def run_kolmogorov_smirnov_test(p_values: pd.Series) -> tuple:
    """
    Perform KS test on p-values against uniform distribution.
    Returns (statistic, p_value).
    """
    # Filter out NaN values
    clean_pvals = p_values.dropna()
    
    if len(clean_pvals) == 0:
        logger.warning("No valid p-values found for KS test.")
        return (0.0, 1.0)
    
    # KS test against uniform(0,1)
    statistic, p_value = kstest(clean_pvals, 'uniform')
    logger.info(f"KS Test: statistic={statistic:.6f}, p_value={p_value:.6f}")
    return (statistic, p_value)

def save_ks_results(statistic: float, p_value: float, output_path: str):
    """
    Save KS test results to JSON file.
    """
    # Determine pass/fail based on p-value < 0.05
    result = "PASS" if p_value < 0.05 else "FAIL"
    
    results = {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "result": result
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved KS test results to {output_path}: {result}")

def main():
    """
    Main entry point for T024: SC-002 Check.
    Performs KS test on unadjusted p-values if no significant taxa found.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Paths
    unadjusted_taxa_pvals_path = get_output_path("data/interim/unadjusted_taxa_pvals.csv")
    ks_results_path = get_output_path("data/processed/ks_test_results.json")
    
    logger.info("Starting SC-002 Check (T024)")
    
    # Load association results
    try:
        df = load_association_results(unadjusted_taxa_pvals_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        raise
    
    # Check for significant taxa
    has_significant = check_significant_taxa(df, q_threshold=0.05)
    
    if has_significant:
        logger.info("Significant taxa found (q < 0.05). SC-002 Check skipped (not needed).")
        # Still write a result indicating the condition was met differently
        import json
        os.makedirs(os.path.dirname(ks_results_path), exist_ok=True)
        results = {
            "statistic": None,
            "p_value": None,
            "result": "SKIPPED_SIGNIFICANT_FOUND",
            "note": "Significant taxa found, KS test not required per SC-002 logic."
        }
        with open(ks_results_path, 'w') as f:
            json.dump(results, f, indent=2)
        return
    
    # No significant taxa found, perform KS test
    logger.info("No significant taxa found. Performing KS test on p-value distribution.")
    
    # Find p-value column
    pval_col = None
    for col in ['pval_raw', 'p_value', 'pval', 'p']:
        if col in df.columns:
            pval_col = col
            break
    
    if pval_col is None:
        logger.error("No unadjusted p-value column found in the data.")
        raise ValueError("Cannot find unadjusted p-value column")
    
    statistic, p_value = run_kolmogorov_smirnov_test(df[pval_col])
    save_ks_results(statistic, p_value, ks_results_path)
    
    logger.info("SC-002 Check completed successfully.")

if __name__ == "__main__":
    main()
