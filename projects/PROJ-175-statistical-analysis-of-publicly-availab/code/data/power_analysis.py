"""
T013b: Pilot Download & Power Analysis
Downloads a small pilot sample of the Recipe1M dataset to estimate variance
and calculate the required sample size for the full analysis.

Parameters:
    alpha=0.05 (significance level)
    beta=0.2 (power=0.8)
    effect_size=0.1 (Cohen's h for proportions or small effect for means)

Output:
    data/pilot_stats.json
"""
import os
import sys
import json
import math
from pathlib import Path
import pandas as pd
from datasets import load_dataset
from datetime import datetime

# Ensure output directory exists
def ensure_directories():
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def download_pilot_sample():
    """
    Downloads a small pilot sample (e.g., 500 recipes) from Recipe1M.
    Uses streaming to avoid loading the full dataset into memory.
    """
    print("Starting pilot download of Recipe1M...")
    try:
        # Load a small subset using streaming
        # Using a small number (500) for pilot estimation
        pilot_size = 500
        
        # Load dataset in streaming mode
        dataset = load_dataset("recipe1m/recipe1m", split="train", streaming=True)
        
        # Take a sample
        pilot_data = []
        count = 0
        for item in dataset:
            if count >= pilot_size:
                break
            pilot_data.append(item)
            count += 1
        
        if count == 0:
            raise ValueError("No data retrieved from pilot download")
        
        print(f"Successfully downloaded {count} recipes for pilot analysis")
        return pd.DataFrame(pilot_data)
        
    except Exception as e:
        # Log failure loudly - no synthetic fallback
        error_code = "HTTP_500" if "http" in str(e).lower() else "UNKNOWN"
        status_file = Path("data/download_status_recipe1m.json")
        status_file.write_text(json.dumps({
            "dataset": "recipe1m",
            "status": "FAILED",
            "error_code": error_code,
            "error_message": str(e)
        }, indent=2))
        raise e

def calculate_variance_estimate(df):
    """
    Estimates variance from the pilot sample.
    For power analysis, we need to estimate the variance of the outcome variable.
    If 'rating' exists, use it. Otherwise, estimate from recipe complexity (num ingredients).
    """
    if df is None or len(df) == 0:
        raise ValueError("Cannot calculate variance from empty dataset")
    
    # Try to use rating if available
    if 'rating' in df.columns:
        # Filter out NaN ratings
        valid_ratings = df['rating'].dropna()
        if len(valid_ratings) > 1:
            variance = valid_ratings.var()
            mean_val = valid_ratings.mean()
            return variance, mean_val, "rating"
    
    # Fallback to ingredient count as proxy for complexity
    if 'ingredients' in df.columns:
        # Calculate number of ingredients per recipe
        ingredient_counts = df['ingredients'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        if len(ingredient_counts) > 1:
            variance = ingredient_counts.var()
            mean_val = ingredient_counts.mean()
            return variance, mean_val, "ingredient_count"
    
    # Last resort: use a very small sample variance estimate
    # This is a conservative estimate for planning purposes
    return 1.0, 1.0, "estimated"

def calculate_sample_size(variance, mean_val, alpha=0.05, beta=0.2, effect_size=0.1):
    """
    Calculates required sample size for a two-sample t-test or similar.
    Uses the formula: n = 2 * (Z_alpha + Z_beta)^2 * sigma^2 / delta^2
    
    Where:
        Z_alpha = 1.96 for alpha=0.05 (two-tailed)
        Z_beta = 0.84 for beta=0.2 (power=0.8)
        delta = effect_size * sigma (if effect_size is standardized)
    """
    # Critical Z values
    z_alpha = 1.96  # for 95% confidence
    z_beta = 0.84   # for 80% power
    
    # If effect_size is standardized (Cohen's d), delta = effect_size * sigma
    # If effect_size is absolute, delta = effect_size
    # Assuming standardized effect size
    delta = effect_size * math.sqrt(variance)
    
    if delta == 0:
        # Avoid division by zero, use a minimal delta
        delta = 0.01 * math.sqrt(variance)
    
    # Sample size per group for two-sample test
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) * variance / (delta ** 2)
    
    # Total sample size
    total_n = int(math.ceil(n_per_group * 2))
    
    # Ensure minimum sample size for statistical validity
    if total_n < 100:
        total_n = 100
        
    return total_n

def main():
    output_dir = ensure_directories()
    output_file = output_dir / "pilot_stats.json"
    
    print("=== T013b: Pilot Download & Power Analysis ===")
    
    # Step 1: Download pilot sample
    pilot_df = download_pilot_sample()
    
    # Step 2: Calculate variance estimate
    variance, mean_val, source = calculate_variance_estimate(pilot_df)
    print(f"Variance estimate: {variance:.4f} (from {source})")
    
    # Step 3: Calculate required sample size
    required_n = calculate_sample_size(variance, mean_val)
    print(f"Required sample size for power=0.8, effect_size=0.1: {required_n}")
    
    # Step 4: Save results
    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "pilot_sample_size": len(pilot_df),
        "variance_estimate": variance,
        "mean_estimate": mean_val,
        "variance_source": source,
        "parameters": {
            "alpha": 0.05,
            "beta": 0.2,
            "power": 0.8,
            "effect_size": 0.1
        },
        "sample_size_required": required_n,
        "status": "SUCCESS"
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Pilot analysis complete. Results saved to {output_file}")
    return result

if __name__ == "__main__":
    main()