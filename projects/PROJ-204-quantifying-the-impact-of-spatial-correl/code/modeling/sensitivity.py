"""
Sensitivity Analysis Module for T031c.

Calculates the impact of excluding depth-confounded samples on correlation
coefficients between spatial metrics and device performance (PCE).

Inputs:
  1. Pre-filter dataset (from T014c): `data/processed/unified_dataset.csv`
  2. Primary analysis dataset (from T034): `data/processed/filtered_dataset.csv`

Outputs:
  - `data/processed/sensitivity_analysis_results.json`: Contains correlation
    coefficients for both datasets, delta (Δr), and sensitivity flag.
  - `data/processed/sensitivity_analysis.csv`: Detailed breakdown of metrics
    and correlations for both datasets.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy.stats import pearsonr, spearmanr
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define expected file paths based on task descriptions
PRE_FILTER_DATASET_PATH = Path("data/processed/unified_dataset.csv")
PRIMARY_DATASET_PATH = Path("data/processed/filtered_dataset.csv")
OUTPUT_JSON_PATH = Path("data/processed/sensitivity_analysis_results.json")
OUTPUT_CSV_PATH = Path("data/processed/sensitivity_analysis.csv")

def load_dataset_safe(path: Path) -> pd.DataFrame:
    """Load a dataset with error handling."""
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded dataset from {path}: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset from {path}: {e}")
        raise

def calculate_correlation(
    df: pd.DataFrame,
    metric_col: str,
    target_col: str
) -> Tuple[Optional[float], Optional[float], int]:
    """
    Calculate Pearson and Spearman correlation coefficients and p-values.
    
    Returns:
      Tuple of (pearson_r, spearman_r, valid_count) or (None, None, 0) if insufficient data.
    """
    # Drop rows with missing values in the relevant columns
    subset = df[[metric_col, target_col]].dropna()
    n = len(subset)
    
    if n < 3:
        logger.warning(f"Insufficient data for correlation on {metric_col} vs {target_col}: n={n}")
        return None, None, n
    
    try:
        # Pearson correlation
        pearson_r, pearson_p = pearsonr(subset[metric_col], subset[target_col])
        
        # Spearman correlation
        spearman_r, spearman_p = spearmanr(subset[metric_col], subset[target_col])
        
        return float(pearson_r), float(spearman_r), n
    except Exception as e:
        logger.error(f"Correlation calculation failed for {metric_col} vs {target_col}: {e}")
        return None, None, n

def run_sensitivity_analysis(
    pre_filter_path: Path = PRE_FILTER_DATASET_PATH,
    primary_path: Path = PRIMARY_DATASET_PATH,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by comparing correlations on pre-filter vs primary datasets.
    
    Args:
        pre_filter_path: Path to the pre-filter dataset (T014c output)
        primary_path: Path to the primary analysis dataset (T034 output)
        config: Configuration dictionary (optional, loaded from default if None)
        
    Returns:
        Dictionary containing analysis results.
    """
    if config is None:
        config = get_config()
    
    # Load datasets
    df_pre = load_dataset_safe(pre_filter_path)
    df_primary = load_dataset_safe(primary_path)
    
    logger.info(f"Pre-filter dataset size: {len(df_pre)}")
    logger.info(f"Primary dataset size: {len(df_primary)}")
    
    # Identify spatial metric columns (assuming standard naming from T019/T022)
    # We look for columns that likely contain correlation_length or spectral_power
    metric_columns = [col for col in df_pre.columns if 'correlation_length' in col or 'spectral_power' in col]
    target_columns = [col for col in df_pre.columns if 'pce' in col.lower() or 'efficiency' in col.lower()]
    
    if not metric_columns:
        logger.warning("No spatial metric columns found. Attempting to find columns with 'length' or 'power'.")
        metric_columns = [col for col in df_pre.columns if 'length' in col or 'power' in col]
    
    if not target_columns:
        raise ValueError("No performance metric columns (PCE/Efficiency) found in dataset.")
    
    target_col = target_columns[0]
    logger.info(f"Target column: {target_col}")
    logger.info(f"Metric columns to analyze: {metric_columns}")
    
    results = {
        "pre_filter_sample_count": len(df_pre),
        "primary_sample_count": len(df_primary),
        "samples_excluded": len(df_pre) - len(df_primary),
        "threshold": config.get("sensitivity", {}).get("delta_r_threshold", 0.1),
        "metrics": {}
    }
    
    summary_rows = []
    
    for metric_col in metric_columns:
        # Calculate for pre-filter
        p_pre, s_pre, n_pre = calculate_correlation(df_pre, metric_col, target_col)
        
        # Calculate for primary
        p_pri, s_pri, n_pri = calculate_correlation(df_primary, metric_col, target_col)
        
        # Calculate Delta
        delta_p = None
        delta_s = None
        high_sensitivity_p = False
        high_sensitivity_s = False
        
        if p_pre is not None and p_pri is not None:
            delta_p = p_pri - p_pre
            high_sensitivity_p = abs(delta_p) > results["threshold"]
        
        if s_pre is not None and s_pri is not None:
            delta_s = s_pri - s_pre
            high_sensitivity_s = abs(delta_s) > results["threshold"]
        
        metric_result = {
            "metric": metric_col,
            "pre_filter": {
                "pearson_r": p_pre,
                "spearman_r": s_pre,
                "n": n_pre
            },
            "primary": {
                "pearson_r": p_pri,
                "spearman_r": s_pri,
                "n": n_pri
            },
            "delta": {
                "pearson_r": delta_p,
                "spearman_r": delta_s
            },
            "sensitivity": {
                "pearson": "High" if high_sensitivity_p else "Low",
                "spearman": "High" if high_sensitivity_s else "Low"
            }
        }
        
        results["metrics"][metric_col] = metric_result
        
        # Add to summary CSV
        summary_rows.append({
            "metric": metric_col,
            "pre_pearson_r": p_pre,
            "pre_spearman_r": s_pre,
            "primary_pearson_r": p_pri,
            "primary_spearman_r": s_pri,
            "delta_pearson_r": delta_p,
            "delta_spearman_r": delta_s,
            "sensitivity_pearson": high_sensitivity_p,
            "sensitivity_spearman": high_sensitivity_s,
            "n_pre": n_pre,
            "n_primary": n_pri
        })
    
    # Determine overall conclusion
    any_high_sensitivity = any(
        m["sensitivity"]["pearson"] == "High" or m["sensitivity"]["spearman"] == "High"
        for m in results["metrics"].values()
    )
    
    results["conclusion"] = {
        "high_sensitivity_detected": any_high_sensitivity,
        "message": (
            "Exclusion of depth-confounded samples significantly alters correlation conclusions."
            if any_high_sensitivity else
            "Correlation conclusions remain stable after excluding depth-confounded samples."
        )
    }
    
    return results, pd.DataFrame(summary_rows)

def main():
    """Main entry point for the sensitivity analysis script."""
    logger.info("Starting Sensitivity Analysis (T031c)...")
    
    try:
        config = get_config()
        results_df, summary_df = run_sensitivity_analysis(config=config)
        
        # Write JSON results
        with open(OUTPUT_JSON_PATH, 'w') as f:
            json.dump(results_df, f, indent=2)
        logger.info(f"Results written to {OUTPUT_JSON_PATH}")
        
        # Write CSV summary
        summary_df.to_csv(OUTPUT_CSV_PATH, index=False)
        logger.info(f"Summary CSV written to {OUTPUT_CSV_PATH}")
        
        # Print summary to console
        print(f"\n--- Sensitivity Analysis Summary ---")
        print(f"Samples excluded: {results_df['samples_excluded']}")
        print(f"High Sensitivity Detected: {results_df['conclusion']['high_sensitivity_detected']}")
        print(f"Conclusion: {results_df['conclusion']['message']}")
        print("--------------------------------------\n")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
