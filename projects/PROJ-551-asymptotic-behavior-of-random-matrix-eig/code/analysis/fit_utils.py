import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy.optimize import curve_fit

from utils.config import get_project_paths

logger = logging.getLogger(__name__)

def sigmoid_function(x, a, b, c):
    """
    Sigmoid function for threshold fitting.
    
    P(outlier) = 1 / (1 + exp(-a * (x - c)))
    
    Where:
      - a: slope parameter
      - b: not used directly, but kept for compatibility
      - c: critical threshold (theta_c)
    
    Returns:
      Sigmoid value at x
    """
    # Clip x to avoid overflow
    x = np.clip(x, -100, 100)
    return 1.0 / (1.0 + np.exp(-a * (x - c)))

def load_mc_results(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load Monte Carlo results from CSV file.
    
    Args:
        csv_path: Path to mc_results.csv
    
    Returns:
        List of result dictionaries
    """
    import csv
    
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "run_id": row["run_id"],
                "N": int(row["N"]),
                "theta": float(row["theta"]),
                "seed": int(row["seed"]),
                "outlier_count": int(row["outlier_count"]),
                "max_eigenvalue": float(row["max_eigenvalue"])
            })
    
    return results

def aggregate_by_theta(
    results: List[Dict[str, Any]],
    n_per_config: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Aggregate results by theta value.
    
    Args:
        results: List of MC result dictionaries
        n_per_config: Expected number of iterations per config (optional)
    
    Returns:
        Tuple of (theta_values, outlier_probabilities, counts)
    """
    # Group by theta
    theta_groups = {}
    for r in results:
        theta = r["theta"]
        if theta not in theta_groups:
            theta_groups[theta] = []
        theta_groups[theta].append(r)
    
    # Compute statistics
    theta_values = []
    outlier_probs = []
    counts = []
    
    for theta in sorted(theta_groups.keys()):
        group = theta_groups[theta]
        total = len(group)
        outliers = sum(1 for r in group if r["outlier_count"] > 0)
        
        prob = outliers / total if total > 0 else 0.0
        
        theta_values.append(theta)
        outlier_probs.append(prob)
        counts.append(total)
    
    return np.array(theta_values), np.array(outlier_probs), np.array(counts)

def fit_critical_threshold(
    theta_values: np.ndarray,
    outlier_probs: np.ndarray,
    p0: Optional[List[float]] = None
) -> Optional[Dict[str, float]]:
    """
    Fit sigmoid to outlier probability data to find critical threshold.
    
    Args:
        theta_values: Array of theta values
        outlier_probs: Array of outlier probabilities
        p0: Initial guess for [a, b, c] (slope, scale, threshold)
    
    Returns:
        Dictionary with fitted parameters, or None if fit fails
    """
    if len(theta_values) < 3:
        logger.warning("Not enough data points for fitting")
        return None
    
    # Filter out exact 0 or 1 probabilities to avoid log issues
    # (though sigmoid handles them, fitting can be unstable)
    mask = (outlier_probs > 0.01) & (outlier_probs < 0.99)
    if np.sum(mask) < 3:
        logger.warning("Not enough intermediate probability points for fitting")
        # Try fitting anyway with all points
        mask = np.ones_like(outlier_probs, dtype=bool)
    
    theta_fit = theta_values[mask]
    prob_fit = outlier_probs[mask]
    
    if p0 is None:
        # Reasonable initial guess: slope=5, threshold=2.0
        p0 = [5.0, 1.0, 2.0]
    
    try:
        popt, pcov = curve_fit(
            sigmoid_function,
            theta_fit,
            prob_fit,
            p0=p0,
            maxfev=5000
        )
        
        a, b, c = popt
        theta_c = c
        
        # Compute confidence intervals (approximate)
        perr = np.sqrt(np.diag(pcov))
        theta_c_err = perr[2]
        
        logger.info(f"Fitted critical threshold: theta_c = {theta_c:.4f} ± {theta_c_err:.4f}")
        
        return {
            "theta_c": float(theta_c),
            "theta_c_error": float(theta_c_err),
            "slope": float(a),
            "slope_error": float(perr[0]),
            "r_squared": None  # Can compute if needed
        }
    
    except Exception as e:
        logger.error(f"Curve fitting failed: {e}", exc_info=True)
        return None

def analyze_threshold_identification(
    mc_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Analyze Monte Carlo results to identify threshold.
    
    Args:
        mc_results_path: Path to mc_results.csv
        output_path: Path to write threshold_identification_raw.json
    
    Returns:
        Analysis results dictionary
    """
    # Load data
    results = load_mc_results(mc_results_path)
    
    # Aggregate by theta
    theta_values, outlier_probs, counts = aggregate_by_theta(results)
    
    # Fit threshold
    fit_result = fit_critical_threshold(theta_values, outlier_probs)
    
    analysis = {
        "theta_values": theta_values.tolist(),
        "outlier_probabilities": outlier_probs.tolist(),
        "counts": counts.tolist(),
        "fit_result": fit_result,
        "metadata": {
            "total_runs": len(results),
            "unique_thetas": len(theta_values),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    logger.info(f"Threshold analysis written to {output_path}")
    
    return analysis

def main():
    """Main entry point for fit_utils."""
    import argparse
    from datetime import datetime, timezone
    
    parser = argparse.ArgumentParser(description="Fit critical threshold from MC results")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/mc_results.csv",
        help="Input MC results CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/threshold_identification_raw.json",
        help="Output analysis JSON"
    )
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    analyze_threshold_identification(args.input, args.output)

if __name__ == "__main__":
    main()
