"""
Sensitivity analysis module for User Story 3.

Implements threshold sweeping for minimum generation counts (3, 4, 5) to assess
the robustness of correlation results against generation threshold choices.

Outputs:
    output/sensitivity_results.json: Structured results of the sweep.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from config import get_env
from analysis.correlation import load_variance_matrix, filter_by_condition, calculate_spearman_correlation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GENERATION_THRESHOLDS = [3, 4, 5]
OUTPUT_PATH = Path("output/sensitivity_results.json")
INPUT_PATH = Path("data/processed/variance_matrix.csv")
CORRELATION_RESULTS_PATH = Path("output/correlation_results.json")

def load_correlation_results() -> Optional[Dict[str, Any]]:
    """Load existing correlation results to extract empirical p-values if available."""
    if not CORRELATION_RESULTS_PATH.exists():
        logger.warning(f"Correlation results file not found at {CORRELATION_RESULTS_PATH}. "
                       "Proceeding without empirical p-values.")
        return None
    
    try:
        with open(CORRELATION_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load correlation results: {e}")
        return None

def filter_by_generation_threshold(
    df: pd.DataFrame, 
    min_generations: int
) -> pd.DataFrame:
    """
    Filter the variance matrix to include only rows with generation count >= threshold.
    
    Args:
        df: The variance matrix DataFrame.
        min_generations: Minimum number of generations required.
        
    Returns:
        Filtered DataFrame.
    """
    if 'generation_count' not in df.columns:
        logger.warning("Column 'generation_count' not found in variance matrix. "
                       "Returning unfiltered data.")
        return df
    
    filtered_df = df[df['generation_count'] >= min_generations]
    logger.info(f"Filtered to {len(filtered_df)} rows for threshold >= {min_generations}")
    return filtered_df

def run_sensitivity_sweep(
    df: pd.DataFrame,
    correlation_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the sensitivity sweep across generation thresholds [3, 4, 5].
    
    For each threshold:
        1. Filter data by generation count.
        2. Calculate Spearman correlation.
        3. Check significance (p < 0.05).
        
    Args:
        df: The variance matrix DataFrame.
        correlation_data: Optional existing correlation results for empirical p-values.
        
    Returns:
        Dictionary containing sweep results.
    """
    results = {
        "thresholds": [],
        "summary": {
            "significant_count": 0,
            "rho_range": None,
            "stability_flag": None,
            "convergence_warning": False
        }
    }
    
    rhos = []
    p_values = []
    significant_count = 0
    
    for threshold in GENERATION_THRESHOLDS:
        logger.info(f"Processing threshold: {threshold} generations")
        
        # Filter data
        filtered_df = filter_by_generation_threshold(df, threshold)
        
        if len(filtered_df) < 2:
            logger.warning(f"Not enough data points for threshold {threshold}. Skipping.")
            results["thresholds"].append({
                "threshold": threshold,
                "sample_size": 0,
                "rho": None,
                "p_value": None,
                "significant": False,
                "status": "insufficient_data"
            })
            continue
        
        # Calculate correlation
        # Ensure we have the correct columns
        if 'epigenetic_variance' not in filtered_df.columns or 'expression_variance' not in filtered_df.columns:
            logger.error("Required columns 'epigenetic_variance' or 'expression_variance' missing.")
            results["thresholds"].append({
                "threshold": threshold,
                "sample_size": len(filtered_df),
                "rho": None,
                "p_value": None,
                "significant": False,
                "status": "missing_columns"
            })
            continue
        
        rho, p_val = calculate_spearman_correlation(
            filtered_df['epigenetic_variance'].dropna(),
            filtered_df['expression_variance'].dropna()
        )
        
        is_significant = p_val < 0.05 if p_val is not None else False
        if is_significant:
            significant_count += 1
        
        rhos.append(rho)
        p_values.append(p_val)
        
        results["thresholds"].append({
            "threshold": threshold,
            "sample_size": len(filtered_df),
            "rho": float(rho) if rho is not None else None,
            "p_value": float(p_val) if p_val is not None else None,
            "significant": is_significant,
            "status": "completed"
        })
    
    # Summary calculations
    if len(rhos) >= 2:
        results["summary"]["rho_range"] = {
            "min": float(min(rhos)),
            "max": float(max(rhos)),
            "delta": float(max(rhos) - min(rhos))
        }
        
        # Stability check: flag if |Δrho| > 0.1
        delta_rho = max(rhos) - min(rhos)
        if delta_rho > 0.1:
            results["summary"]["stability_flag"] = "unstable"
            logger.warning(f"Correlation unstable: |Δrho| = {delta_rho:.3f} > 0.1")
        else:
            results["summary"]["stability_flag"] = "stable"
    else:
        results["summary"]["rho_range"] = None
        results["summary"]["stability_flag"] = "insufficient_data_for_stability_check"
    
    # Check significance consistency: flag if significant in < 2 of 3 thresholds
    results["summary"]["significant_count"] = significant_count
    if significant_count < 2:
        results["summary"]["robustness_flag"] = "not_robust"
        logger.warning(f"Result not robust: significant in only {significant_count}/3 thresholds")
    else:
        results["summary"]["robustness_flag"] = "robust"
    
    return results

def save_results(results: Dict[str, Any]) -> None:
    """Save sensitivity results to JSON file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved sensitivity results to {OUTPUT_PATH}")

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Main entry point for sensitivity analysis.
    
    Returns:
        Dictionary containing the full sensitivity analysis results.
    """
    logger.info("Starting sensitivity analysis for generation thresholds")
    
    # Load variance matrix
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input variance matrix not found at {INPUT_PATH}. "
                                "Run preprocessing pipeline first.")
    
    df = load_variance_matrix()
    logger.info(f"Loaded variance matrix with {len(df)} rows")
    
    # Load existing correlation results for context (optional)
    correlation_data = load_correlation_results()
    
    # Run sweep
    results = run_sensitivity_sweep(df, correlation_data)
    
    # Save results
    save_results(results)
    
    return results

def main():
    """Command-line entry point."""
    try:
        results = run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed successfully")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
