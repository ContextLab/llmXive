import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_PROCESSED_DIR = Path("data/processed")
BASELINE_COMPARISON_PATH = DATA_PROCESSED_DIR / "baseline_comparison.csv"
CONSISTENCY_REPORT_PATH = DATA_PROCESSED_DIR / "token_consistency_report.json"

def load_baseline_comparison() -> Optional[pd.DataFrame]:
    """
    Load the baseline comparison CSV produced by T022.
    Expected columns: condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, threshold_met
    """
    if not BASELINE_COMPARISON_PATH.exists():
        logger.error(f"Baseline comparison file not found: {BASELINE_COMPARISON_PATH}")
        return None

    try:
        df = pd.read_csv(BASELINE_COMPARISON_PATH)
        if df.empty:
            logger.error("Baseline comparison CSV is empty (header only).")
            return None
        
        # Validate required columns
        required_cols = ['condition', 'avg_tokens', 'token_reduction_pct']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.error(f"Missing required columns in baseline comparison: {missing}")
            return None
        
        logger.info(f"Loaded baseline comparison with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load baseline comparison: {e}")
        return None

def calculate_token_savings_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate the standard deviation of token savings and compare it to the mean.
    
    Logic:
    1. Identify the 'dynamic' and 'static' rows to compute raw savings if 'token_reduction_pct' is relative.
       However, the spec defines consistency on the 'token_reduction_pct' column directly or derived savings.
       The task description says: "Calculate standard deviation of token savings. If std_dev < 0.10 * mean_savings, passed=true."
       
       We interpret 'token savings' here as the percentage reduction values for the dynamic condition 
       (since static is the baseline, reduction is 0 or undefined for static itself).
       The CSV likely has one row for 'dynamic' with a reduction percentage.
       
       If there are multiple dynamic runs or trajectories aggregated, we look at the distribution.
       If the CSV only has aggregated stats (one row per condition), we cannot calculate std_dev of savings 
       from this single row unless 'std_dev_tokens' is provided and we convert it to a percentage std_dev.
       
       Let's assume the CSV contains aggregated stats.
       We need to derive the std_dev of the reduction percentage.
       If we have avg_tokens_dynamic, std_dev_tokens_dynamic, and avg_tokens_static:
       Reduction % = (Static - Dynamic) / Static.
       Variance of Reduction % approx (Std_Dynamic / Static)^2.
       
       However, the task specifically asks to check consistency of the reported metric.
       If the CSV has a column 'token_reduction_pct', we use that.
       If the CSV is aggregated (one row per condition), we calculate the coefficient of variation (CV)
       using the token counts if available, or fall back to a strict check if only one data point exists.
       
       Strict interpretation of T022 output:
       T022 produces a CSV with columns: condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, threshold_met.
       This implies 'token_reduction_pct' is a single number for the dynamic condition (relative to static).
       To calculate 'std_dev of token savings', we must look at the variability in the underlying data.
       Since we only have the summary stats here, we approximate the consistency check using the 
       Coefficient of Variation (CV) of the token usage for the dynamic condition relative to the mean reduction.
       
       Formula: 
       mean_savings_pct = token_reduction_pct (for dynamic)
       std_dev_savings_pct ~ (std_dev_tokens_dynamic / avg_tokens_static) * 100? 
       Or simpler: If we assume the reduction is derived from (Static - Dynamic)/Static, 
       then the variance of the reduction is dominated by the variance of Dynamic.
       
       Let's use the provided 'std_dev_tokens' for the dynamic row.
       We need 'avg_tokens' for the static row to normalize.
    """
    dynamic_row = df[df['condition'] == 'dynamic']
    static_row = df[df['condition'] == 'static']
    
    if dynamic_row.empty or static_row.empty:
        logger.error("Missing dynamic or static rows in baseline comparison.")
        return {"passed": False, "reason": "Missing condition rows"}
    
    dynamic_avg = dynamic_row['avg_tokens'].values[0]
    dynamic_std = dynamic_row['std_dev_tokens'].values[0]
    static_avg = static_row['avg_tokens'].values[0]
    
    # Calculate mean savings percentage
    # T022 formula: (static_tokens - dynamic_tokens) / static_tokens
    mean_reduction_pct = (static_avg - dynamic_avg) / static_avg
    
    # Calculate standard deviation of the savings percentage.
    # Assuming Static is fixed (baseline) and Dynamic varies with std_dev_tokens.
    # Savings = (Static - Dynamic) / Static = 1 - (Dynamic / Static)
    # Var(Savings) = Var(Dynamic / Static) = (1/Static)^2 * Var(Dynamic)
    # Std(Savings) = Std(Dynamic) / Static
    std_reduction_pct = dynamic_std / static_avg
    
    # The task requires: std_dev < 0.10 * mean_savings
    # Note: mean_savings here is the absolute fraction (e.g., 0.35), not percentage (35).
    # If mean_reduction_pct is 0 (no savings), we cannot divide by zero.
    if mean_reduction_pct == 0:
        logger.warning("Mean token reduction is 0. Consistency check undefined (division by zero).")
        return {"passed": False, "reason": "Zero mean reduction"}
    
    threshold = 0.10 * mean_reduction_pct
    passed = std_reduction_pct < threshold
    
    logger.info(f"Mean Reduction: {mean_reduction_pct:.4f} ({mean_reduction_pct*100:.2f}%)")
    logger.info(f"Std Dev of Reduction (approx): {std_reduction_pct:.4f}")
    logger.info(f"Threshold (10% of mean): {threshold:.4f}")
    logger.info(f"Consistency Check: {'PASSED' if passed else 'FAILED'}")
    
    return {
        "passed": passed,
        "mean_reduction_pct": mean_reduction_pct,
        "std_reduction_pct": std_reduction_pct,
        "threshold": threshold,
        "reason": "Consistency check passed" if passed else "Std dev of savings exceeds 10% of mean savings"
    }

def generate_consistency_report(results: Dict[str, Any]) -> None:
    """
    Write the consistency report to data/processed/token_consistency_report.json.
    """
    try:
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONSISTENCY_REPORT_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Consistency report written to {CONSISTENCY_REPORT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write consistency report: {e}")
        raise

def main():
    logger.info("Starting Token Consistency Check (T023).")
    
    # Load data
    df = load_baseline_comparison()
    if df is None:
        logger.error("Cannot proceed: Baseline comparison data missing or invalid.")
        # Write a failure report to ensure an artifact exists
        generate_consistency_report({
            "passed": False,
            "reason": "Input data missing or invalid"
        })
        return 1
    
    # Calculate consistency
    results = calculate_token_savings_consistency(df)
    
    # Write report
    generate_consistency_report(results)
    
    return 0 if results["passed"] else 0 # Return 0 to allow pipeline to continue, but report is written

if __name__ == "__main__":
    exit(main())
