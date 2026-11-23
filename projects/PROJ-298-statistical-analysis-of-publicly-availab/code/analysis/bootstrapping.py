import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Constants
BOOTSTRAP_ITERATIONS = 1000
BLOCK_LENGTH = 12  # 12 months to preserve annual seasonality as per Plan.md
RANDOM_SEED = 42
CONFIDENCE_LEVEL = 0.95

def load_processed_data() -> Dict[str, Any]:
    """Load the preprocessed monthly frequency data."""
    data_path = Path("data/processed/monthly_frequencies.json")
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        return json.load(f)

def load_trend_results() -> Dict[str, Any]:
    """Load the trend analysis results containing Theil-Sen slopes."""
    data_path = Path("data/processed/trend_intermediate.json")
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        return json.load(f)

def theil_sen_slope(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate the Theil-Sen estimator for the slope of a linear trend.
    
    Args:
        x: Independent variable (time indices)
        y: Dependent variable (frequencies)
    
    Returns:
        The median of all slopes between pairs of points.
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

def block_bootstrap_sample(time_series: np.ndarray, block_length: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate a bootstrap sample using the block bootstrap method.
    
    This preserves temporal autocorrelation by sampling contiguous blocks of data.
    The block length of 12 months is chosen to preserve annual seasonality patterns.
    
    Args:
        time_series: The original time series data.
        block_length: Length of each block (12 months).
        rng: Random number generator.
    
    Returns:
        A bootstrap sample of the same length as the input.
    """
    n = len(time_series)
    if n < block_length:
        raise ValueError(f"Time series length ({n}) must be >= block_length ({block_length})")
    
    # Calculate number of blocks needed
    num_blocks = math.ceil(n / block_length)
    
    # Sample blocks with replacement
    sampled_blocks = []
    for _ in range(num_blocks):
        start_idx = rng.integers(0, n - block_length + 1)
        block = time_series[start_idx : start_idx + block_length]
        sampled_blocks.append(block)
    
    # Concatenate blocks and truncate to original length
    bootstrap_sample = np.concatenate(sampled_blocks)[:n]
    return bootstrap_sample

def bootstrap_theil_sen(
    time_series: np.ndarray,
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    block_length: int = BLOCK_LENGTH,
    random_seed: int = RANDOM_SEED
) -> Tuple[float, float, float]:
    """
    Calculate confidence intervals for Theil-Sen slope using block bootstrap.
    
    Args:
        time_series: The time series data to bootstrap.
        n_iterations: Number of bootstrap iterations.
        block_length: Length of blocks for block bootstrap (12 months).
        random_seed: Seed for reproducibility.
    
    Returns:
        Tuple of (median_slope, lower_ci, upper_ci) for 95% confidence interval.
    """
    rng = np.random.default_rng(random_seed)
    n = len(time_series)
    x = np.arange(n)
    
    slopes = []
    for _ in range(n_iterations):
        # Generate bootstrap sample
        bootstrap_sample = block_bootstrap_sample(time_series, block_length, rng)
        
        # Calculate Theil-Sen slope for this sample
        slope = theil_sen_slope(x, bootstrap_sample)
        slopes.append(slope)
    
    slopes = np.array(slopes)
    median_slope = float(np.median(slopes))
    
    # Calculate confidence intervals
    alpha = 1 - CONFIDENCE_LEVEL
    lower_idx = int((alpha / 2) * n_iterations)
    upper_idx = int((1 - alpha / 2) * n_iterations)
    
    lower_ci = float(np.percentile(slopes, (alpha / 2) * 100))
    upper_ci = float(np.percentile(slopes, (1 - alpha / 2) * 100))
    
    return median_slope, lower_ci, upper_ci

def save_confidence_intervals(
    results: Dict[str, Any],
    output_path: str = "data/processed/confidence_interval.json"
) -> None:
    """
    Save confidence interval results to a JSON file.
    
    Args:
        results: Dictionary containing confidence interval results.
        output_path: Path to the output file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

def run_bootstrapping_analysis(
    data: Dict[str, Any],
    trend_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run the bootstrapping analysis for all tags in the dataset.
    
    Args:
        data: Preprocessed monthly frequency data.
        trend_results: Trend analysis results containing Theil-Sen slopes.
    
    Returns:
        Dictionary containing confidence interval results for all tags.
    """
    results = {
        "metadata": {
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "block_length_months": BLOCK_LENGTH,
            "confidence_level": CONFIDENCE_LEVEL,
            "random_seed": RANDOM_SEED,
            "description": "Block bootstrap confidence intervals for Theil-Sen slopes. "
                           "Block length of 12 months preserves annual seasonality patterns."
        },
        "tag_results": {}
    }
    
    # Get list of tags from trend results
    tags = trend_results.get("tags", [])
    
    for tag_info in tags:
        tag_name = tag_info.get("tag")
        if not tag_name or tag_name not in data.get("tags", {}):
            continue
        
        time_series = np.array(data["tags"][tag_name]["monthly_frequencies"])
        
        if len(time_series) < BLOCK_LENGTH:
            results["tag_results"][tag_name] = {
                "tag": tag_name,
                "status": "insufficient_data",
                "reason": f"Time series length ({len(time_series)}) < block length ({BLOCK_LENGTH})"
            }
            continue
        
        try:
            median_slope, lower_ci, upper_ci = bootstrap_theil_sen(time_series)
            
            results["tag_results"][tag_name] = {
                "tag": tag_name,
                "theil_sen_slope": median_slope,
                "confidence_interval": {
                    "lower": lower_ci,
                    "upper": upper_ci,
                    "level": CONFIDENCE_LEVEL
                },
                "status": "success"
            }
        except Exception as e:
            results["tag_results"][tag_name] = {
                "tag": tag_name,
                "status": "error",
                "error_message": str(e)
            }
    
    return results

def main() -> None:
    """Main entry point for the bootstrapping analysis."""
    print("Starting bootstrapping analysis for Theil-Sen slope confidence intervals...")
    print(f"Using {BOOTSTRAP_ITERATIONS} iterations with block length of {BLOCK_LENGTH} months")
    print("(Block length chosen to preserve annual seasonality patterns)")
    
    try:
        # Load data
        print("Loading preprocessed data...")
        data = load_processed_data()
        print(f"Loaded data for {len(data.get('tags', {}))} tags")
        
        print("Loading trend results...")
        trend_results = load_trend_results()
        print(f"Loaded trend results for {len(trend_results.get('tags', []))} tags")
        
        # Run analysis
        print("Running bootstrapping analysis...")
        results = run_bootstrapping_analysis(data, trend_results)
        
        # Save results
        output_path = "data/processed/confidence_interval.json"
        print(f"Saving results to {output_path}...")
        save_confidence_intervals(results, output_path)
        
        # Verify output
        if Path(output_path).exists():
            with open(output_path, 'r') as f:
                verify_data = json.load(f)
            print(f"Successfully saved confidence intervals for {len(verify_data.get('tag_results', {}))} tags")
            print("Verification: File exists and contains valid 95% CI bounds.")
        else:
            raise RuntimeError(f"Failed to create output file: {output_path}")
        
        print("Bootstrapping analysis completed successfully.")
        
    except FileNotFoundError as e:
        print(f"ERROR: Required data file not found: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
