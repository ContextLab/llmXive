import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "monthly_tag_frequencies.json"
TREND_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "trend_results.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "confidence_interval.json"

def load_processed_data() -> Dict[str, Any]:
    """Load the preprocessed monthly tag frequencies."""
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_PATH}. "
            "Run T013 (preprocess.py) first."
        )
    with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_trend_results() -> Dict[str, Any]:
    """Load the trend analysis results (slopes, p-values, classifications)."""
    if not TREND_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Trend results not found at {TREND_RESULTS_PATH}. "
            "Run T014 (trends.py) first."
        )
    with open(TREND_RESULTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def theil_sen_slope(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate the Theil-Sen estimator for slope.
    Median of all slopes between pairs of points.
    """
    n = len(x)
    if n < 2:
        return 0.0
    
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            if x[j] != x[i]:
                slope = (y[j] - y[i]) / (x[j] - x[i])
                slopes.append(slope)
    
    if not slopes:
        return 0.0
    return float(np.median(slopes))

def bootstrap_theil_sen(
    x: np.ndarray, 
    y: np.ndarray, 
    n_iterations: int = 1000, 
    random_seed: Optional[int] = None,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Perform bootstrapping to calculate confidence intervals for Theil-Sen slope.
    
    Args:
        x: Independent variable (time points)
        y: Dependent variable (frequencies)
        n_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)
    
    Returns:
        Dictionary with 'slope', 'ci_lower', 'ci_upper', 'ci_width'
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    n = len(x)
    bootstrap_slopes = []
    
    # Bootstrap sampling
    for _ in range(n_iterations):
        # Resample indices with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        # Sort by x to maintain time order for Theil-Sen calculation
        sort_idx = np.argsort(x_boot)
        x_boot_sorted = x_boot[sort_idx]
        y_boot_sorted = y_boot[sort_idx]
        
        # Calculate Theil-Sen slope for bootstrap sample
        slope = theil_sen_slope(x_boot_sorted, y_boot_sorted)
        bootstrap_slopes.append(slope)
    
    bootstrap_slopes = np.array(bootstrap_slopes)
    
    # Calculate percentile confidence intervals
    alpha = 1 - confidence_level
    ci_lower = float(np.percentile(bootstrap_slopes, (alpha / 2) * 100))
    ci_upper = float(np.percentile(bootstrap_slopes, (1 - alpha / 2) * 100))
    
    return {
        "slope": float(np.median(bootstrap_slopes)),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "ci_width": ci_upper - ci_lower,
        "n_iterations": n_iterations,
        "confidence_level": confidence_level
    }

def save_confidence_intervals(results: Dict[str, Any], output_path: Path) -> None:
    """Save confidence interval results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

def run_bootstrapping_analysis(
    processed_data: Dict[str, Any],
    trend_results: Dict[str, Any],
    n_iterations: int = 1000,
    random_seed: int = 42,
    confidence_level: float = 0.95,
    min_data_points: int = 5
) -> Dict[str, Any]:
    """
    Run bootstrapping analysis for all tags in the trend results.
    
    Args:
        processed_data: Preprocessed monthly tag frequencies
        trend_results: Results from trend analysis (T014)
        n_iterations: Number of bootstrap iterations
        random_seed: Random seed for reproducibility
        confidence_level: Confidence level for CIs
        min_data_points: Minimum number of data points required
    
    Returns:
        Dictionary mapping tag names to confidence interval results
    """
    results = {}
    
    # Get tags from trend results
    tags_to_analyze = list(trend_results.keys())
    
    for tag in tags_to_analyze:
        if tag not in processed_data.get("data", {}):
            continue
        
        tag_data = processed_data["data"][tag]
        months = tag_data.get("months", [])
        frequencies = tag_data.get("frequencies", [])
        
        if len(months) < min_data_points:
            results[tag] = {
                "status": "insufficient_data",
                "reason": f"Only {len(months)} data points, minimum {min_data_points} required",
                "n_data_points": len(months)
            }
            continue
        
        # Convert months to numeric time points (0, 1, 2, ...)
        x = np.arange(len(months), dtype=float)
        y = np.array(frequencies, dtype=float)
        
        # Run bootstrapping
        ci_result = bootstrap_theil_sen(
            x, y, 
            n_iterations=n_iterations,
            random_seed=random_seed,
            confidence_level=confidence_level
        )
        
        # Add metadata
        ci_result["tag"] = tag
        ci_result["n_data_points"] = len(months)
        
        # Check if trend is significant (from trend_results if available)
        if tag in trend_results:
            ci_result["trend_classification"] = trend_results[tag].get("classification", "Unknown")
            ci_result["p_value"] = trend_results[tag].get("p_value", None)
        
        results[tag] = ci_result
    
    return results

def main() -> None:
    """Main entry point for bootstrapping analysis."""
    print("Starting bootstrapping analysis for Theil-Sen slopes...")
    
    # Load data
    print(f"Loading processed data from {PROCESSED_DATA_PATH}...")
    processed_data = load_processed_data()
    
    print(f"Loading trend results from {TREND_RESULTS_PATH}...")
    trend_results = load_trend_results()
    
    # Run analysis
    print("Running bootstrapping analysis (this may take a while)...")
    results = run_bootstrapping_analysis(
        processed_data,
        trend_results,
        n_iterations=1000,
        random_seed=42,
        confidence_level=0.95,
        min_data_points=5
    )
    
    # Save results
    print(f"Saving confidence intervals to {OUTPUT_PATH}...")
    save_confidence_intervals(results, OUTPUT_PATH)
    
    # Summary
    total_tags = len(results)
    successful = sum(1 for r in results.values() if r.get("status") != "insufficient_data")
    insufficient = total_tags - successful
    
    print(f"\nBootstrapping analysis complete!")
    print(f"  Total tags analyzed: {total_tags}")
    print(f"  Successful analyses: {successful}")
    print(f"  Insufficient data: {insufficient}")
    print(f"  Output saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
