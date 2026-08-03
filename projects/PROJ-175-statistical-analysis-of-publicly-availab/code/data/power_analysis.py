import os
import sys
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np
from datasets import load_dataset

# Ensure directories exist
def ensure_directories():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "raw").mkdir(exist_ok=True)
    (data_dir / "processed").mkdir(exist_ok=True)

def download_pilot_sample(output_path: Path, max_recipes: int = 5000):
    """
    Streams a small pilot sample from Recipe1M to estimate variance.
    Uses Recipe1M-Ratings as the proxy source for ingredient/rating data
    as per the Plan's Critical Reframe (T012a logic).
    """
    print(f"Downloading pilot sample (max {max_recipes} recipes)...")
    
    # Use the verified source: Recipe1M-Ratings from HuggingFace
    # This is the real, programmatically accessible source.
    dataset = load_dataset("thiagob/recipe1m-ratings", split="train", streaming=True)
    
    samples = []
    count = 0
    
    for row in dataset:
        if count >= max_recipes:
            break
        
        # Extract relevant fields for pilot analysis
        # The dataset typically has 'ingredients' (list) and 'rating' (float)
        if 'ingredients' in row and 'rating' in row:
            samples.append({
                'recipe_id': count,
                'num_ingredients': len(row['ingredients']),
                'rating': float(row['rating']) if row['rating'] is not None else 0.0
            })
            count += 1
        
        if count % 1000 == 0:
            print(f"  Fetched {count} recipes...")

    if not samples:
        raise RuntimeError("Failed to fetch any pilot samples from Recipe1M-Ratings.")
    
    df = pd.DataFrame(samples)
    df.to_parquet(output_path, index=False)
    print(f"Pilot sample saved to {output_path} ({len(df)} recipes).")
    return df

def calculate_variance_estimate(df: pd.DataFrame, target_column: str = 'num_ingredients') -> float:
    """
    Calculates the variance of the target column from the pilot sample.
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in pilot data.")
    
    var = df[target_column].var()
    if pd.isna(var):
        return 0.0
    return float(var)

def calculate_sample_size(variance: float, effect_size: float = 0.1, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculates the required sample size for a statistical test (t-test approximation).
    
    Formula: n = 2 * ((Z_alpha + Z_beta)^2 * sigma^2) / delta^2
    Where:
      sigma^2 = variance
      delta = effect_size * sigma (Cohen's d logic, but here we assume effect_size is absolute difference if provided, 
      or we treat effect_size as the standardized difference. 
      The task specifies "effect size >= 0.1". In power analysis contexts, 'effect size' usually refers to Cohen's d.
      If effect_size is Cohen's d, then delta = d * sigma.
      Then n = 2 * ((Z_alpha + Z_beta)^2 * sigma^2) / (d^2 * sigma^2) = 2 * (Z_alpha + Z_beta)^2 / d^2.
      
      Let's assume effect_size = 0.1 is the standardized difference (Cohen's d).
    """
    # Z values for normal distribution
    # Z_alpha for two-tailed 0.05 is approx 1.96
    # Z_beta for power 0.8 (beta=0.2) is approx 0.84
    from scipy.stats import norm
    
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)
    
    # If effect_size is Cohen's d (standardized), the sigma cancels out in the numerator/denominator
    # n = 2 * (z_alpha + z_beta)^2 / d^2
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")
    
    n = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
    return int(math.ceil(n))

def main():
    ensure_directories()
    
    pilot_path = Path("data/pilot_sample.parquet")
    output_path = Path("data/pilot_stats.json")
    
    try:
        # 1. Download pilot sample
        df = download_pilot_sample(pilot_path)
        
        # 2. Estimate variance (using number of ingredients as a proxy for complexity/size)
        variance = calculate_variance_estimate(df, 'num_ingredients')
        print(f"Estimated variance (num_ingredients): {variance}")
        
        # 3. Calculate required sample size
        # Parameters from task: effect_size >= 0.1, power >= 0.8
        required_n = calculate_sample_size(variance, effect_size=0.1, power=0.8)
        
        # 4. Save results
        stats = {
            "pilot_sample_size": len(df),
            "variance_estimate": variance,
            "effect_size_target": 0.1,
            "power_target": 0.8,
            "sample_size_required": required_n,
            "pilot_file": str(pilot_path),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Power analysis complete. Required sample size: {required_n}")
        print(f"Results saved to {output_path}")
        
    except Exception as e:
        # Fail loudly as per constraints
        print(f"ERROR: Pilot download or analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()