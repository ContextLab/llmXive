"""
Analysis module for Lottery Draw Integrity.
Implements correlation analysis, tier analysis, and outlier sensitivity.
"""
import json
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
METRICS_FILE = "data/processed/metrics.json"
CORRELATION_RESULT_FILE = "data/results/correlation_result.json"
JACKPOT_COLUMN = "jackpot_amount"
PRIMARY_METRIC = "birthday_cluster_ratio"
SECONDARY_METRIC = "consecutive_pattern_count"

def load_processed_metrics(filepath: str = METRICS_FILE) -> List[Dict[str, Any]]:
    """
    Load processed metrics from JSON file.
    Expects a list of dictionaries, each representing a draw with metrics.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and "draws" in data:
        return data["draws"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unexpected metrics file format. Expected list of draws or dict with 'draws' key.")

def compute_correlation_continuous(data: List[Dict[str, Any]], method: str = 'spearman') -> Dict[str, Any]:
    """
    Compute correlation between jackpot_amount and uniformity metrics.
    
    Args:
        data: List of dictionaries containing draw data (jackpot_amount, metrics).
        method: Correlation method ('spearman' or 'pearson').
    
    Returns:
        Dictionary containing correlation results for each metric.
    """
    if not data:
        logger.warning("Empty dataset provided for correlation analysis.")
        return {}

    df = pd.DataFrame(data)
    
    # Check if required columns exist
    if JACKPOT_COLUMN not in df.columns:
        raise ValueError(f"Column '{JACKPOT_COLUMN}' not found in data.")
    
    # Identify metric columns (exclude jackpot and non-numeric)
    metric_cols = [col for col in df.columns if col != JACKPOT_COLUMN and np.issubdtype(df[col].dtype, np.number)]
    
    if not metric_cols:
        logger.warning("No numeric metric columns found for correlation.")
        return {}

    results = {}
    
    for col in metric_cols:
        # Drop rows where either jackpot or metric is NaN
        valid_data = df[[JACKPOT_COLUMN, col]].dropna()
        
        if len(valid_data) < 3:
            logger.warning(f"Insufficient data for correlation on '{col}': {len(valid_data)} rows.")
            results[col] = {
                "correlation": None,
                "p_value": None,
                "n_samples": len(valid_data)
            }
            continue
        
        x = valid_data[JACKPOT_COLUMN]
        y = valid_data[col]
        
        if method == 'spearman':
            corr, p_val = stats.spearmanr(x, y)
        elif method == 'pearson':
            corr, p_val = stats.pearsonr(x, y)
        else:
            raise ValueError(f"Unknown correlation method: {method}")
        
        results[col] = {
            "correlation": float(corr),
            "p_value": float(p_val),
            "n_samples": len(valid_data),
            "method": method
        }
    
    return results

def run_tier_analysis(data: List[Dict[str, Any]], tier_column: str = "jackpot_amount") -> Dict[str, Any]:
    """
    Bin data into Small/Medium/Large tiers and compute metrics per tier.
    """
    if not data:
        return {}
    
    df = pd.DataFrame(data)
    
    # Define tiers based on quantiles or fixed thresholds
    # Simple quantile-based approach: 33rd and 66th percentiles
    q33 = df[tier_column].quantile(0.33)
    q66 = df[tier_column].quantile(0.66)
    
    def assign_tier(val):
        if val <= q33:
            return "Small"
        elif val <= q66:
            return "Medium"
        else:
            return "Large"
    
    df["tier"] = df[tier_column].apply(assign_tier)
    
    tier_results = {}
    for tier, group in df.groupby("tier"):
        # Compute mean metric for this tier
        metric_cols = [col for col in group.columns if col != tier_column and col != "tier" and np.issubdtype(group[col].dtype, np.number)]
        tier_stats = {}
        for col in metric_cols:
            mean_val = group[col].mean()
            count = len(group)
            tier_stats[col] = {"mean": float(mean_val), "count": count}
        
        tier_results[tier] = tier_stats
    
    return tier_results

def compute_outlier_sensitivity(data: List[Dict[str, Any]], threshold_factor: float = 10.0) -> Dict[str, Any]:
    """
    Compute correlation with and without extreme outliers (jackpots > threshold_factor * mean).
    Returns the delta in correlation coefficient.
    """
    if not data:
        return {"delta": None, "full_result": None, "filtered_result": None}
    
    df = pd.DataFrame(data)
    mean_jackpot = df[JACKPOT_COLUMN].mean()
    outlier_threshold = mean_jackpot * threshold_factor
    
    # Full dataset correlation
    full_results = compute_correlation_continuous(data, method='spearman')
    
    # Filtered dataset (remove outliers)
    filtered_data = df[df[JACKPOT_COLUMN] <= outlier_threshold].to_dict('records')
    filtered_results = compute_correlation_continuous(filtered_data, method='spearman')
    
    # Calculate delta for primary metric
    delta = {}
    for metric in [PRIMARY_METRIC, SECONDARY_METRIC]:
        if metric in full_results and metric in filtered_results:
            r_full = full_results[metric].get("correlation")
            r_filt = filtered_results[metric].get("correlation")
            if r_full is not None and r_filt is not None:
                delta[metric] = abs(r_full - r_filt)
            else:
                delta[metric] = None
        else:
            delta[metric] = None
    
    return {
        "delta": delta,
        "outlier_threshold": float(outlier_threshold),
        "n_outliers": len(df[df[JACKPOT_COLUMN] > outlier_threshold]),
        "n_total": len(df)
    }

def generate_warnings(data: List[Dict[str, Any]], warnings_config: Optional[Dict] = None) -> List[Dict[str, str]]:
    """
    Generate warnings based on data characteristics (e.g., insufficient data in tiers).
    """
    warnings_list = []
    df = pd.DataFrame(data)
    
    # Check for missing sales data if column exists
    if "total_sales" in df.columns:
        missing_sales = df["total_sales"].isna().sum()
        if missing_sales > 0:
            warnings_list.append({
                "type": "missing_sales",
                "reason": f"Missing total_sales data for {missing_sales} draws."
            })
    
    # Check for small sample sizes in tiers
    # (This is a simplified check; detailed tier analysis is in run_tier_analysis)
    
    return warnings_list

def main():
    """
    Main entry point for correlation analysis.
    """
    logger.info("Starting correlation analysis...")
    
    try:
        # Load data
        data = load_processed_metrics()
        logger.info(f"Loaded {len(data)} draws.")
        
        # Compute correlations
        correlation_results = compute_correlation_continuous(data, method='spearman')
        logger.info(f"Correlation results: {correlation_results}")
        
        # Tier analysis
        tier_results = run_tier_analysis(data)
        logger.info(f"Tier analysis results: {tier_results}")
        
        # Outlier sensitivity
        sensitivity_results = compute_outlier_sensitivity(data)
        logger.info(f"Sensitivity results: {sensitivity_results}")
        
        # Warnings
        warnings_list = generate_warnings(data)
        
        # Aggregate output
        output = {
            "correlation_results": correlation_results,
            "tier_analysis": tier_results,
            "outlier_sensitivity_delta": sensitivity_results.get("delta", {}),
            "warnings": warnings_list,
            "control_variable_note": "Quick Pick rate unobservable; no control applied"
        }
        
        # Save output
        os.makedirs(os.path.dirname(CORRELATION_RESULT_FILE), exist_ok=True)
        with open(CORRELATION_RESULT_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Results saved to {CORRELATION_RESULT_FILE}")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()