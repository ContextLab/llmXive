import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
from scipy import stats

from data.utils import setup_logging, set_seed, get_seed

logger = logging.getLogger(__name__)

def wilcoxon_signed_rank_test(sample1: np.ndarray, sample2: np.ndarray) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test between two paired samples.
    
    Args:
        sample1: First sample (e.g., GNN errors)
        sample2: Second sample (e.g., RF errors)
        
    Returns:
        Dictionary with 'statistic' and 'pvalue'
    """
    if len(sample1) != len(sample2):
        raise ValueError("Samples must be of equal length for paired test")
    if len(sample1) < 2:
        raise ValueError("Samples must have at least 2 elements")
        
    statistic, pvalue = stats.wilcoxon(sample1, sample2)
    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue)
    }

def run_wilcoxon_on_metrics(
    gnns_errors: List[float], 
    rf_errors: List[float]
) -> Dict[str, Any]:
    """
    Run Wilcoxon test on lists of errors.
    
    Args:
        gnns_errors: List of errors from GNN model
        rf_errors: List of errors from Random Forest model
        
    Returns:
        Result dictionary from wilcoxon_signed_rank_test
    """
    arr1 = np.array(gnns_errors)
    arr2 = np.array(rf_errors)
    return wilcoxon_signed_rank_test(arr1, arr2)

def calculate_vif(descriptors: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        descriptors: 2D numpy array of shape (n_samples, n_features)
        feature_names: Optional list of feature names
        
    Returns:
        Dictionary mapping feature names (or indices) to VIF values
    """
    n_samples, n_features = descriptors.shape
    if n_samples <= n_features:
        raise ValueError("Need more samples than features for VIF calculation")
        
    vif_results = {}
    X = descriptors
    
    # Add intercept column for regression
    X_with_intercept = np.column_stack([np.ones(n_samples), X])
    
    for i in range(n_features):
        # Regress feature i against all other features
        y = X[:, i]
        # All other features (excluding i)
        other_features_indices = [j for j in range(n_features) if j != i]
        X_other = X[:, other_features_indices]
        
        # Add intercept
        X_other_with_intercept = np.column_stack([np.ones(n_samples), X_other])
        
        # Fit linear regression: y = b0 + b1*x1 + ... + bn*xn
        try:
            coeffs, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)
            if len(residuals) > 0:
                rss = residuals[0]
                # Total sum of squares
                tss = np.sum((y - np.mean(y))**2)
                if tss == 0:
                    vif = float('inf')
                else:
                    r_squared = 1 - (rss / tss)
                    if r_squared >= 1.0:
                        vif = float('inf')
                    else:
                        vif = 1.0 / (1.0 - r_squared)
            else:
                # Fallback if residuals empty (perfect fit or singular)
                vif = float('inf')
        except np.linalg.LinAlgError:
            vif = float('inf')
            
        name = feature_names[i] if feature_names else f"feature_{i}"
        vif_results[name] = float(vif)
        
    return vif_results

def sensitivity_analysis_sweep(
    kfold_results_path: str,
    output_path: str,
    thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping R² thresholds.
    
    Logic:
    1. Load k-fold cross-validation results (list of R² scores).
    2. For each threshold in {0.25, 0.30, 0.35}:
       - Calculate successful_prediction_rate = (count where R² > threshold) / total
    3. Calculate stability_metric = std(successful_prediction_rate across thresholds).
    4. Save results to JSON.
    
    Args:
        kfold_results_path: Path to JSON file containing k-fold R² scores.
        output_path: Path to write the sensitivity sweep JSON.
        thresholds: List of thresholds to sweep (default: [0.25, 0.30, 0.35])
        
    Returns:
        Dictionary containing the full sweep results.
    """
    if thresholds is None:
        thresholds = [0.25, 0.30, 0.35]
        
    # Load k-fold results
    if not os.path.exists(kfold_results_path):
        raise FileNotFoundError(f"K-fold results file not found: {kfold_results_path}")
        
    with open(kfold_results_path, 'r') as f:
        kfold_data = json.load(f)
        
    # Extract R² scores. Assume structure: {"r2_scores": [...]} or similar
    r2_scores = []
    if "r2_scores" in kfold_data:
        r2_scores = kfold_data["r2_scores"]
    elif isinstance(kfold_data, list):
        # If it's just a list of scores
        r2_scores = kfold_data
    else:
        # Try to find any list of floats
        for key, val in kfold_data.items():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], (int, float)):
                r2_scores = val
                break
                
    if not r2_scores:
        raise ValueError("Could not extract R² scores from k-fold results file")
        
    r2_array = np.array(r2_scores)
    total_count = len(r2_array)
    
    logger.info(f"Loaded {total_count} R² scores from {kfold_results_path}")
    
    results = []
    successful_rates = []
    
    for thresh in thresholds:
        # Count predictions where R² > threshold
        count = np.sum(r2_array > thresh)
        rate = count / total_count if total_count > 0 else 0.0
        
        results.append({
            "threshold": float(thresh),
            "successful_prediction_rate": float(rate),
            "count": int(count),
            "total": int(total_count)
        })
        successful_rates.append(rate)
        
    # Calculate stability metric: std of successful_prediction_rate across the sweep
    stability_metric = float(np.std(successful_rates))
    
    output_data = {
        "thresholds": thresholds,
        "results": results,
        "stability_metric": stability_metric,
        "metric": "r2"
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Sensitivity sweep results written to {output_path}")
    logger.info(f"Stability metric (std of rates): {stability_metric:.4f}")
    
    return output_data

def main():
    """
    Entry point for sensitivity analysis.
    Expects k-fold results at code/evaluation/results/kfold_cv_results.json
    Outputs to code/evaluation/results/sensitivity_sweep.json
    """
    setup_logging()
    
    # Paths relative to project root (code/ directory context)
    # Assuming script runs from code/ or we adjust paths accordingly
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kfold_path = os.path.join(base_dir, "evaluation", "results", "kfold_cv_results.json")
    output_path = os.path.join(base_dir, "evaluation", "results", "sensitivity_sweep.json")
    
    # If kfold path doesn't exist, check alternative locations or fail
    if not os.path.exists(kfold_path):
        # Try relative to current working directory if running as script
        kfold_path_alt = "evaluation/results/kfold_cv_results.json"
        if os.path.exists(kfold_path_alt):
            kfold_path = kfold_path_alt
        else:
            logger.error(f"K-fold results not found at {kfold_path} or {kfold_path_alt}")
            # Fallback to a placeholder path if we are just testing structure, 
            # but per strict rules, we must fail if real data isn't there.
            # However, T031 should have produced this. If missing, we fail.
            raise FileNotFoundError(f"Required input file not found: {kfold_path}")
    
    try:
        sensitivity_analysis_sweep(kfold_path, output_path)
        print(f"Sensitivity analysis complete. Results saved to {output_path}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()