import os
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Ensure we can import from the project root if run as a module
# The API surface indicates this file is at code/analysis/bootstrapping.py
# and imports should be relative to the project structure or standard lib.

def load_processed_data(filepath: str = "data/processed/tag_frequencies.json") -> Dict[str, Any]:
    """Load the preprocessed tag frequency data."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_trend_results(filepath: str = "data/processed/trend_intermediate.json") -> Dict[str, Any]:
    """Load the trend analysis intermediate results."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Trend results file not found: {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def theil_sen_slope(x: List[float], y: List[float]) -> float:
    """
    Calculate the Theil-Sen estimator for slope.
    This is the median of all pairwise slopes.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 points with matching x and y lengths.")
    
    slopes = []
    n = len(x)
    for i in range(n):
        for j in range(i + 1, n):
            if x[j] != x[i]:
                slope = (y[j] - y[i]) / (x[j] - x[i])
                slopes.append(slope)
    
    if not slopes:
        return 0.0
    
    slopes.sort()
    mid = len(slopes) // 2
    if len(slopes) % 2 == 0:
        return (slopes[mid - 1] + slopes[mid]) / 2.0
    else:
        return slopes[mid]

def bootstrap_theil_sen(
    x: List[float], 
    y: List[float], 
    n_iterations: int = 1000, 
    seed: int = 42,
    sample_fraction: float = 0.8
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence intervals for the Theil-Sen slope.
    
    Args:
        x: Independent variable values (e.g., time indices)
        y: Dependent variable values (e.g., frequencies)
        n_iterations: Number of bootstrap iterations
        seed: Random seed for reproducibility
        sample_fraction: Fraction of data to sample in each iteration
        
    Returns:
        Tuple of (slope_estimate, lower_ci, upper_ci)
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    
    random.seed(seed)
    n = len(x)
    sample_size = max(2, int(n * sample_fraction))
    
    bootstrap_slopes = []
    
    for _ in range(n_iterations):
        # Resample with replacement
        indices = [random.randint(0, n - 1) for _ in range(sample_size)]
        x_sample = [x[i] for i in indices]
        y_sample = [y[i] for i in indices]
        
        # Calculate Theil-Sen slope for this sample
        try:
            slope = theil_sen_slope(x_sample, y_sample)
            bootstrap_slopes.append(slope)
        except ValueError:
            # Skip if sample doesn't have enough variance
            continue
    
    if not bootstrap_slopes:
        raise RuntimeError("Bootstrap failed: no valid slopes calculated.")
    
    bootstrap_slopes.sort()
    
    # Calculate 95% CI (2.5th and 97.5th percentiles)
    lower_idx = int(0.025 * len(bootstrap_slopes))
    upper_idx = int(0.975 * len(bootstrap_slopes))
    
    lower_ci = bootstrap_slopes[lower_idx]
    upper_ci = bootstrap_slopes[upper_idx]
    
    # Calculate median slope from bootstrap distribution
    mid = len(bootstrap_slopes) // 2
    if len(bootstrap_slopes) % 2 == 0:
        slope_estimate = (bootstrap_slopes[mid - 1] + bootstrap_slopes[mid]) / 2.0
    else:
        slope_estimate = bootstrap_slopes[mid]
    
    return slope_estimate, lower_ci, upper_ci

def save_confidence_intervals(
    results: Dict[str, Any], 
    filepath: str = "data/processed/confidence_interval.json"
) -> None:
    """Save confidence interval results to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

def run_bootstrapping_analysis(
    data: Dict[str, Any], 
    trend_results: Dict[str, Any],
    n_iterations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full bootstrapping analysis for all tags in the trend results.
    
    Args:
        data: Preprocessed tag frequency data
        trend_results: Intermediate trend analysis results
        n_iterations: Number of bootstrap iterations
        seed: Random seed
        
    Returns:
        Dictionary containing confidence interval results for all tags
    """
    results = {
        "metadata": {
            "n_iterations": n_iterations,
            "seed": seed,
            "confidence_level": 0.95,
            "method": "Bootstrap Theil-Sen"
        },
        "tags": {}
    }
    
    # Get the tags from trend results
    tags_to_analyze = trend_results.get("tags", {})
    
    for tag_name, tag_data in tags_to_analyze.items():
        # Extract time series data
        # The data structure from preprocess should have 'monthly_data' or similar
        # We need to map this to x (time) and y (frequency)
        
        # Assuming structure: { "monthly_data": { "2020-01": 100, "2020-02": 105, ... } }
        monthly_data = tag_data.get("monthly_data", {})
        
        if not monthly_data:
            # Try alternative key names
            monthly_data = tag_data.get("data", {})
        
        if not monthly_data:
            # Skip if no data found
            continue
        
        # Convert to sorted lists
        sorted_months = sorted(monthly_data.keys())
        x_values = list(range(len(sorted_months)))  # Time indices
        y_values = [monthly_data[month] for month in sorted_months]
        
        # Need at least 2 points
        if len(x_values) < 2:
            continue
        
        try:
            slope_estimate, lower_ci, upper_ci = bootstrap_theil_sen(
                x_values, y_values, n_iterations, seed
            )
            
            results["tags"][tag_name] = {
                "slope_estimate": slope_estimate,
                "ci_lower": lower_ci,
                "ci_upper": upper_ci,
                "n_iterations_used": len(y_values),
                "n_months": len(sorted_months)
            }
        except Exception as e:
            # Log error but continue with other tags
            results["tags"][tag_name] = {
                "error": str(e),
                "status": "failed"
            }
    
    return results

def main():
    """Main entry point for the bootstrapping analysis."""
    # Define paths relative to project root
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data"
    
    processed_data_file = data_path / "processed" / "tag_frequencies.json"
    trend_results_file = data_path / "processed" / "trend_intermediate.json"
    output_file = data_path / "processed" / "confidence_interval.json"
    
    print(f"Loading processed data from: {processed_data_file}")
    if not processed_data_file.exists():
        # Try alternative path if running from different directory
        processed_data_file = Path("data/processed/tag_frequencies.json")
    
    if not processed_data_file.exists():
        print(f"Error: Processed data file not found at {processed_data_file}")
        print("Please ensure T013 (preprocess) has been completed.")
        return 1
    
    print(f"Loading trend results from: {trend_results_file}")
    if not trend_results_file.exists():
        trend_results_file = Path("data/processed/trend_intermediate.json")
    
    if not trend_results_file.exists():
        print(f"Error: Trend results file not found at {trend_results_file}")
        print("Please ensure T014 (trends) has been completed.")
        return 1
    
    try:
        data = load_processed_data(str(processed_data_file))
        trend_results = load_trend_results(str(trend_results_file))
        
        print(f"Running bootstrapping analysis with 1000 iterations...")
        results = run_bootstrapping_analysis(data, trend_results, n_iterations=1000, seed=42)
        
        print(f"Saving results to: {output_file}")
        save_confidence_intervals(results, str(output_file))
        
        # Verify the file was created and is valid
        if Path(output_file).exists():
            with open(output_file, 'r') as f:
                check_results = json.load(f)
            
            if "tags" in check_results and len(check_results["tags"]) > 0:
                print(f"Successfully calculated confidence intervals for {len(check_results['tags'])} tags.")
                print("Verification: data/processed/confidence_interval.json exists and contains valid data.")
                return 0
            else:
                print("Warning: Output file created but contains no tag results.")
                return 1
        else:
            print("Error: Failed to create output file.")
            return 1
            
    except Exception as e:
        print(f"Error during bootstrapping analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
