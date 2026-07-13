import json
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from scipy.stats import spearmanr
from data_utils import load_draws_csv
from exceptions import LotteryDataError, MissingSalesError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_metrics(filepath: str = "data/processed/metrics.json") -> Dict[str, Any]:
    """
    Load processed metrics from JSON file.
    Merges with raw draw data to ensure we have jackpot amounts for tier analysis.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def compute_correlation_continuous(dataframe: pd.DataFrame, method: str = 'spearman') -> Dict[str, Any]:
    """
    Compute correlation between jackpot_amount and uniformity metrics.
    """
    try:
        if method == 'spearman':
            corr, p_value = spearmanr(dataframe['jackpot_amount'], dataframe['birthday_cluster_ratio'])
        else:
            # Fallback to pearson if requested, though spearman is preferred for non-normal data
            corr, p_value = np.corrcoef(dataframe['jackpot_amount'], dataframe['birthday_cluster_ratio'])[0, 1]
            # Approximate p-value for pearson (simplified)
            n = len(dataframe)
            t_stat = corr * np.sqrt((n - 2) / (1 - corr**2))
            from scipy.stats import t
            p_value = 2 * (1 - t.cdf(abs(t_stat), n - 2))

        return {
            "correlation_coefficient": float(corr),
            "p_value": float(p_value),
            "control_variable_note": "Quick Pick rate unobservable; no control applied"
        }
    except Exception as e:
        logger.error(f"Error computing correlation: {e}")
        return {
            "correlation_coefficient": None,
            "p_value": None,
            "control_variable_note": "Quick Pick rate unobservable; no control applied",
            "error": str(e)
        }

def run_tier_analysis(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Implement binning by 'Small/Medium/Large' tiers.
    Requirement: Spec US-2 Acceptance Scenario 1.
    Output: Nested key 'tier_analysis' in correlation result.
    
    Logic:
    1. Calculate global mean of jackpot_amount.
    2. Define thresholds:
       - Small: < 0.5 * mean
       - Medium: 0.5 * mean <= amount <= 1.5 * mean
       - Large: > 1.5 * mean
    3. For each tier, compute count, mean correlation (if multiple tiers exist in a draw? No, one draw per row),
       and mean birthday_cluster_ratio.
    4. Return structure for aggregation.
    """
    import pandas as pd
    
    if 'jackpot_amount' not in dataframe.columns or 'birthday_cluster_ratio' not in dataframe.columns:
        logger.warning("Missing required columns for tier analysis. Returning empty tiers.")
        return {"Small": {}, "Medium": {}, "Large": {}}

    # Handle missing values
    df_clean = dataframe[['jackpot_amount', 'birthday_cluster_ratio']].dropna()
    
    if df_clean.empty:
        logger.warning("No valid data for tier analysis after dropping NaNs.")
        return {"Small": {}, "Medium": {}, "Large": {}}

    mean_jackpot = df_clean['jackpot_amount'].mean()
    
    # Define bins
    # Small: 0 to 0.5 * mean
    # Medium: 0.5 * mean to 1.5 * mean
    # Large: > 1.5 * mean
    
    bins = [0, 0.5 * mean_jackpot, 1.5 * mean_jackpot, float('inf')]
    labels = ['Small', 'Medium', 'Large']
    
    df_clean = df_clean.copy()
    df_clean['tier'] = pd.cut(df_clean['jackpot_amount'], bins=bins, labels=labels, include_lowest=True)
    
    tier_results = {}
    
    for tier in labels:
        tier_data = df_clean[df_clean['tier'] == tier]
        count = len(tier_data)
        
        if count > 0:
            # Calculate stats for this tier
            avg_ratio = tier_data['birthday_cluster_ratio'].mean()
            avg_jackpot = tier_data['jackpot_amount'].mean()
            min_jackpot = tier_data['jackpot_amount'].min()
            max_jackpot = tier_data['jackpot_amount'].max()
            
            tier_results[tier] = {
                "draw_count": count,
                "avg_birthday_cluster_ratio": float(avg_ratio),
                "avg_jackpot_amount": float(avg_jackpot),
                "jackpot_range": {
                    "min": float(min_jackpot),
                    "max": float(max_jackpot)
                },
                "threshold_range": {
                    "lower": float(bins[labels.index(tier)]) if labels.index(tier) > 0 else 0.0,
                    "upper": float(bins[labels.index(tier) + 1]) if labels.index(tier) < len(labels) else float('inf')
                }
            }
        else:
            tier_results[tier] = {
                "draw_count": 0,
                "avg_birthday_cluster_ratio": None,
                "avg_jackpot_amount": None,
                "note": "No draws in this tier"
            }
    
    return tier_results

def compute_outlier_sensitivity(dataframe: pd.DataFrame) -> float:
    """
    Run analysis with and without extreme jackpots (> 10x global mean).
    Return absolute difference in correlation coefficient.
    """
    if 'jackpot_amount' not in dataframe.columns or 'birthday_cluster_ratio' not in dataframe.columns:
        return 0.0

    mean_jackpot = dataframe['jackpot_amount'].mean()
    threshold = 10 * mean_jackpot
    
    df_full = dataframe.dropna(subset=['jackpot_amount', 'birthday_cluster_ratio'])
    df_filtered = df_full[df_full['jackpot_amount'] <= threshold]
    
    if len(df_full) < 2 or len(df_filtered) < 2:
        logger.warning("Insufficient data for outlier sensitivity analysis.")
        return 0.0
    
    corr_full, _ = spearmanr(df_full['jackpot_amount'], df_full['birthday_cluster_ratio'])
    corr_filtered, _ = spearmanr(df_filtered['jackpot_amount'], df_filtered['birthday_cluster_ratio'])
    
    return float(abs(corr_full - corr_filtered))

def generate_warnings(dataframe: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Flag tiers with < 5 draws as "Insufficient Data".
    """
    warnings = []
    import pandas as pd
    
    if 'jackpot_amount' not in dataframe.columns:
        return warnings
        
    mean_jackpot = dataframe['jackpot_amount'].mean()
    bins = [0, 0.5 * mean_jackpot, 1.5 * mean_jackpot, float('inf')]
    labels = ['Small', 'Medium', 'Large']
    
    df_clean = dataframe[['jackpot_amount']].dropna()
    df_clean = df_clean.copy()
    df_clean['tier'] = pd.cut(df_clean['jackpot_amount'], bins=bins, labels=labels, include_lowest=True)
    
    for tier in labels:
        count = len(df_clean[df_clean['tier'] == tier])
        if count < 5:
            warnings.append({
                "type": "insufficient_data",
                "reason": f"Tier '{tier}' has only {count} draws (threshold: 5)"
            })
    
    return warnings

def main():
    """
    Main entry point to run correlation analysis and tier binning.
    Reads from data/processed/metrics.json and data/raw/lottery_draws.csv.
    Outputs to data/results/correlation_result.json.
    """
    import pandas as pd
    
    logger.info("Starting correlation analysis with tier binning (T018b)...")
    
    # Load raw draws to get jackpot amounts
    raw_file = "data/raw/lottery_draws.csv"
    if not os.path.exists(raw_file):
        logger.error(f"Raw data file not found: {raw_file}")
        sys.exit(1)
    
    try:
        df_raw = load_draws_csv(raw_file)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
    
    # Load processed metrics
    metrics_file = "data/processed/metrics.json"
    if not os.path.exists(metrics_file):
        logger.error(f"Processed metrics file not found: {metrics_file}")
        sys.exit(1)
    
    metrics = load_processed_metrics(metrics_file)
    
    # Merge data
    # Assume metrics is a list of dicts or a dict with 'draws' key. 
    # Based on T011, it likely contains a list of draw metrics.
    # We need to align by draw_id or index.
    
    df_metrics = pd.DataFrame(metrics.get('draws', []))
    
    if 'draw_id' in df_raw.columns and 'draw_id' in df_metrics.columns:
        df_merged = pd.merge(df_raw, df_metrics, on='draw_id', how='inner')
    else:
        # Fallback to index if draw_id missing
        df_merged = pd.concat([df_raw, df_metrics], axis=1)
    
    # Run Tier Analysis (T018b)
    logger.info("Running tier analysis...")
    tier_results = run_tier_analysis(df_merged)
    
    # Run Correlation (T016a)
    logger.info("Computing correlation...")
    corr_result = compute_correlation_continuous(df_merged)
    
    # Outlier Sensitivity (T018)
    logger.info("Computing outlier sensitivity...")
    outlier_delta = compute_outlier_sensitivity(df_merged)
    
    # Warnings (T017)
    logger.info("Generating warnings...")
    warnings_list = generate_warnings(df_merged)
    
    # Assemble final result
    final_output = {
        "correlation_coefficient": corr_result.get("correlation_coefficient"),
        "p_value": corr_result.get("p_value"),
        "control_variable_note": corr_result.get("control_variable_note"),
        "outlier_sensitivity_delta": outlier_delta,
        "warnings": warnings_list,
        "tier_analysis": tier_results
    }
    
    # Save to data/results/correlation_result.json
    output_path = "data/results/correlation_result.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return final_output

if __name__ == "__main__":
    main()
