import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Ensure the path is relative to the project root when running as a module
# We assume the script is run from the project root or code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_processed_data() -> Dict[str, Any]:
    """
    Loads the preprocessed monthly frequency data from data/processed/processed_data.json.
    Returns a dictionary mapping tag names to their monthly time series.
    """
    input_path = DATA_PROCESSED_DIR / "processed_data.json"
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found at {input_path}. "
                                "Run T013 (preprocess.py) first.")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def load_trend_results() -> Dict[str, Any]:
    """
    Loads the trend analysis results from data/processed/trend_intermediate.json.
    Returns a dictionary containing slopes, p-values, and classifications.
    """
    input_path = DATA_PROCESSED_DIR / "trend_intermediate.json"
    if not input_path.exists():
        raise FileNotFoundError(f"Trend intermediate results not found at {input_path}. "
                                "Run T014 (trends.py) first.")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def theil_sen_slope(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculates the Theil-Sen estimator slope for a given set of (x, y) points.
    The slope is the median of all slopes between pairs of points.
    """
    n = len(x)
    if n < 2:
        return 0.0
    
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            if dx != 0:
                dy = y[j] - y[i]
                slopes.append(dy / dx)
    
    if not slopes:
        return 0.0
    
    return float(np.median(slopes))


def bootstrap_theil_sen(
    x: np.ndarray, 
    y: np.ndarray, 
    n_iterations: int = 1000, 
    sample_size: Optional[int] = None,
    random_seed: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculates the 95% confidence interval for the Theil-Sen slope using bootstrapping.
    
    Args:
        x: Independent variable array (time indices)
        y: Dependent variable array (frequencies)
        n_iterations: Number of bootstrap iterations
        sample_size: Number of samples to draw in each iteration (default: len(x))
        random_seed: Random seed for reproducibility
    
    Returns:
        Tuple of (original_slope, lower_bound_95ci, upper_bound_95ci)
    """
    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    n = len(x)
    if sample_size is None:
        sample_size = n
    
    # Calculate original slope
    original_slope = theil_sen_slope(x, y)
    
    # Bootstrap resampling
    bootstrap_slopes = []
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=sample_size, replace=True)
        x_sample = x[indices]
        y_sample = y[indices]
        
        # Sort by x to ensure correct ordering for Theil-Sen
        sort_indices = np.argsort(x_sample)
        x_sample = x_sample[sort_indices]
        y_sample = y_sample[sort_indices]
        
        # Calculate slope for resampled data
        slope = theil_sen_slope(x_sample, y_sample)
        bootstrap_slopes.append(slope)
    
    # Calculate 95% confidence interval
    bootstrap_slopes = np.array(bootstrap_slopes)
    lower_bound = float(np.percentile(bootstrap_slopes, 2.5))
    upper_bound = float(np.percentile(bootstrap_slopes, 97.5))
    
    return original_slope, lower_bound, upper_bound


def save_confidence_intervals(results: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the confidence interval results to a JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)


def run_bootstrapping_analysis(
    n_iterations: int = 1000,
    random_seed: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Runs the bootstrapping analysis for all tags in the trend results.
    
    Args:
        n_iterations: Number of bootstrap iterations per tag
        random_seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing confidence interval results for each tag
    """
    # Load data
    processed_data = load_processed_data()
    trend_results = load_trend_results()
    
    confidence_interval_results = {
        "metadata": {
            "n_iterations": n_iterations,
            "random_seed": random_seed,
            "confidence_level": 0.95,
            "method": "Theil-Sen with Bootstrap"
        },
        "tags": {}
    }
    
    # Process each tag
    for tag_name, trend_info in trend_results.get("tags", {}).items():
        # Get the time series for this tag
        if tag_name not in processed_data.get("tags", {}):
            continue
        
        time_series = processed_data["tags"][tag_name]
        if not time_series or len(time_series) < 2:
            continue
        
        # Prepare x (time indices) and y (frequencies)
        # x is the month index (0, 1, 2, ...)
        x = np.arange(len(time_series))
        y = np.array([ts["frequency"] for ts in time_series])
        
        # Remove NaN values if any
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 2:
            continue
        
        # Run bootstrapping
        try:
            slope, lower_ci, upper_ci = bootstrap_theil_sen(
                x, y, 
                n_iterations=n_iterations, 
                random_seed=random_seed
            )
            
            confidence_interval_results["tags"][tag_name] = {
                "slope": slope,
                "confidence_interval_95": {
                    "lower": lower_ci,
                    "upper": upper_ci
                },
                "interval_width": upper_ci - lower_ci,
                "n_points": len(x)
            }
        except Exception as e:
            # Log error but continue with other tags
            print(f"Warning: Bootstrapping failed for tag '{tag_name}': {e}")
            continue
    
    return confidence_interval_results


def main():
    """
    Main entry point for the bootstrapping analysis.
    """
    print("Starting bootstrapping analysis for Theil-Sen slopes...")
    
    # Configuration
    N_ITERATIONS = 1000  # Can be adjusted based on compute budget
    RANDOM_SEED = 42
    
    # Run analysis
    results = run_bootstrapping_analysis(
        n_iterations=N_ITERATIONS,
        random_seed=RANDOM_SEED
    )
    
    # Save results
    output_path = DATA_PROCESSED_DIR / "confidence_interval.json"
    save_confidence_intervals(results, output_path)
    
    print(f"Confidence intervals saved to {output_path}")
    print(f"Processed {len(results['tags'])} tags")
    
    # Summary statistics
    if results["tags"]:
        slopes = [v["slope"] for v in results["tags"].values()]
        avg_interval_width = np.mean([v["interval_width"] for v in results["tags"].values()])
        print(f"Average slope: {np.mean(slopes):.6f}")
        print(f"Average 95% CI width: {avg_interval_width:.6f}")
    
    return results


if __name__ == "__main__":
    main()
