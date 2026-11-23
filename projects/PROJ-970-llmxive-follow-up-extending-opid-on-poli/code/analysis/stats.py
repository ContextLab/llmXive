"""
Statistical analysis module for OPID routing complexity experiments.

Implements regression analysis and statistical tests required for US3.
"""

import json
import os
import logging
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

from config import ensure_directories, get_config_summary
from utils.logging_setup import get_experiment_logger

logger = get_experiment_logger(__name__)

def run_entropy_regression(
    input_path: str,
    output_path: str,
    threshold_col: str = "threshold",
    entropy_col: str = "action_entropy",
    tier_col: str = "tier",
    aggregate_by: Tuple[str, ...] = ("tier", "threshold")
) -> Dict[str, Any]:
    """
    Perform a quadratic regression of action entropy vs threshold.
    
    This function loads episode results, aggregates entropy by (tier, threshold),
    fits a quadratic model (entropy = a*threshold^2 + b*threshold + c) for each tier,
    and outputs the coefficients to a JSON file.
    
    Args:
        input_path: Path to the episode results CSV file.
        output_path: Path to write the regression results JSON.
        threshold_col: Column name for the threshold values.
        entropy_col: Column name for the action entropy values.
        tier_col: Column name for the tier identifier.
        aggregate_by: Tuple of columns to aggregate by before regression.
        
    Returns:
        Dictionary containing regression coefficients for each tier.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing or data is insufficient.
    """
    # Ensure output directory exists
    ensure_directories()
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = [threshold_col, entropy_col, tier_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Data loaded: {len(df)} rows, {df.shape[1]} columns")
    
    # Aggregate entropy by tier and threshold
    # We calculate the mean entropy for each (tier, threshold) combination
    agg_df = df.groupby(aggregate_by, as_index=False)[entropy_col].mean()
    
    logger.info(f"Aggregated data: {len(agg_df)} rows")
    
    # Get unique tiers
    tiers = sorted(agg_df[tier_col].unique())
    
    results = {
        "input_file": input_path,
        "model": "quadratic_regression",
        "equation": "entropy = a * threshold^2 + b * threshold + c",
        "tiers": {}
    }
    
    for tier in tiers:
        tier_data = agg_df[agg_df[tier_col] == tier].copy()
        tier_data = tier_data.sort_values(threshold_col)
        
        thresholds = tier_data[threshold_col].values
        entropies = tier_data[entropy_col].values
        
        logger.info(f"Tier {tier}: {len(thresholds)} data points for regression")
        
        if len(thresholds) < 3:
            logger.warning(f"Tier {tier} has insufficient data points (<3) for quadratic regression. Skipping.")
            results["tiers"][str(tier)] = {
                "status": "skipped",
                "reason": "insufficient_data",
                "data_points": len(thresholds)
            }
            continue
        
        # Perform quadratic regression using numpy.polyfit
        # polyfit returns coefficients in descending order of power: [a, b, c]
        # for a polynomial of degree 2: a*x^2 + b*x + c
        try:
            coeffs = np.polyfit(thresholds, entropies, 2)
            a, b, c = coeffs
            
            # Calculate R-squared for quality check
            p = np.poly1d(coeffs)
            y_pred = p(thresholds)
            ss_res = np.sum((entropies - y_pred) ** 2)
            ss_tot = np.sum((entropies - np.mean(entropies)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            results["tiers"][str(tier)] = {
                "status": "success",
                "coefficients": {
                    "a": float(a),
                    "b": float(b),
                    "c": float(c)
                },
                "equation": f"entropy = {a:.6f} * threshold^2 + {b:.6f} * threshold + {c:.6f}",
                "r_squared": float(r_squared),
                "data_points": int(len(thresholds)),
                "threshold_range": [float(thresholds.min()), float(thresholds.max())]
            }
            
            logger.info(f"Tier {tier}: a={a:.6f}, b={b:.6f}, c={c:.6f}, R²={r_squared:.4f}")
            
        except Exception as e:
            logger.error(f"Regression failed for Tier {tier}: {e}")
            results["tiers"][str(tier)] = {
                "status": "error",
                "error": str(e)
            }
    
    # Write results to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Regression results written to {output_path}")
    return results

def main():
    """Main entry point for running entropy regression analysis."""
    # Default paths
    config = get_config_summary()
    input_path = config.get("episode_results_path", "data/processed/episode_results.csv")
    output_path = config.get("entropy_regression_path", "data/processed/entropy_regression.json")
    
    logger.info("Starting entropy regression analysis (T027b)")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        results = run_entropy_regression(input_path, output_path)
        
        # Summary of results
        successful_tiers = [
            t for t, data in results["tiers"].items() 
            if data.get("status") == "success"
        ]
        logger.info(f"Completed regression for {len(successful_tiers)} tiers: {successful_tiers}")
        
        if not successful_tiers:
            logger.warning("No successful regressions performed. Check input data.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Ensure episode_results.csv has been generated by the experiment runner (T024, T031).")
        raise
    except Exception as e:
        logger.error(f"Error during regression analysis: {e}")
        raise

if __name__ == "__main__":
    main()