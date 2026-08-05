import os
import sys
import json
import math
from pathlib import Path
import pandas as pd
import numpy as np
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def download_pilot_sample(pilot_size=1000):
    """
    Download a small pilot sample of Recipe1M to estimate variance.
    Uses streaming to avoid loading the full dataset into memory.
    
    Args:
        pilot_size (int): Number of recipes to sample for pilot analysis.
        
    Returns:
        pd.DataFrame: Pilot sample dataframe.
    """
    logger.info(f"Downloading pilot sample of {pilot_size} recipes from Recipe1M...")
    
    try:
        # Load Recipe1M dataset in streaming mode
        dataset = load_dataset("recipe1m", split="train", streaming=True)
        
        # Sample a small subset
        pilot_data = []
        count = 0
        for item in dataset:
            if count >= pilot_size:
                break
            pilot_data.append(item)
            count += 1
        
        if not pilot_data:
            raise ValueError("Failed to retrieve any recipes from the dataset.")
        
        df = pd.DataFrame(pilot_data)
        logger.info(f"Successfully downloaded {len(df)} recipes for pilot analysis.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to download pilot sample: {e}")
        raise

def calculate_variance_estimate(df):
    """
    Calculate variance estimate from the pilot sample.
    Uses the variance of the 'rating' column (or a proxy if unavailable).
    
    Args:
        df (pd.DataFrame): Pilot dataset.
        
    Returns:
        float: Estimated variance.
    """
    # Identify a numeric column for variance estimation
    # Prefer 'rating' if available, otherwise use a proxy like recipe length
    if 'rating' in df.columns:
        target_col = 'rating'
    elif 'calories' in df.columns:
        target_col = 'calories'
    else:
        # Fallback: use length of ingredients list as a proxy for variability
        if 'ingredients' in df.columns:
            df['ingredient_count'] = df['ingredients'].apply(lambda x: len(x) if isinstance(x, list) else 0)
            target_col = 'ingredient_count'
        else:
            raise ValueError("No suitable numeric column found for variance estimation.")
    
    # Calculate variance, handling non-numeric data
    numeric_series = pd.to_numeric(df[target_col], errors='coerce').dropna()
    if len(numeric_series) < 2:
        raise ValueError("Insufficient data points to calculate variance.")
    
    variance = numeric_series.var()
    logger.info(f"Estimated variance for column '{target_col}': {variance:.4f}")
    return variance

def calculate_sample_size(variance, alpha=0.05, beta=0.2, effect_size=0.1):
    """
    Calculate the required sample size for a power analysis.
    Uses the formula for a two-sample t-test (or logistic regression approximation):
    n = 2 * ((Z_alpha + Z_beta) / effect_size)^2 * variance
    
    Args:
        variance (float): Estimated variance from pilot data.
        alpha (float): Significance level (default 0.05).
        beta (float): Type II error rate (default 0.2, power=0.8).
        effect_size (float): Minimum detectable effect size (Cohen's d approx).
        
    Returns:
        int: Required sample size.
    """
    # Z-scores for alpha and beta
    z_alpha = 1.96  # For two-tailed alpha=0.05
    z_beta = 0.84   # For power=0.8 (beta=0.2)
    
    # Calculate sample size per group (simplified formula)
    # n = 2 * ( (Z_alpha + Z_beta)^2 * variance ) / (effect_size^2)
    # Note: For logistic regression, this is an approximation.
    # A more precise formula involves the proportion of outcomes, but this serves as a pilot estimate.
    
    numerator = 2 * ( (z_alpha + z_beta)**2 * variance )
    denominator = effect_size**2
    
    n = numerator / denominator
    n = math.ceil(n)
    
    logger.info(f"Calculated required sample size: {n}")
    return n

def main():
    """Main entry point for T013b: Pilot Download & Power Analysis."""
    logger.info("Starting T013b: Pilot Download & Power Analysis")
    
    # 1. Ensure directories
    output_dir = ensure_directories()
    
    # 2. Download pilot sample
    try:
        pilot_df = download_pilot_sample(pilot_size=1000)
    except Exception as e:
        logger.error(f"Pilot download failed: {e}")
        sys.exit(1)
    
    # 3. Calculate variance estimate
    try:
        variance = calculate_variance_estimate(pilot_df)
    except Exception as e:
        logger.error(f"Variance calculation failed: {e}")
        sys.exit(1)
    
    # 4. Calculate required sample size
    try:
        sample_size = calculate_sample_size(variance, alpha=0.05, beta=0.2, effect_size=0.1)
    except Exception as e:
        logger.error(f"Sample size calculation failed: {e}")
        sys.exit(1)
    
    # 5. Save results
    result = {
        "pilot_sample_size": len(pilot_df),
        "variance_estimate": float(variance),
        "sample_size_required": sample_size,
        "parameters": {
            "alpha": 0.05,
            "power": 0.8,
            "effect_size": 0.1
        },
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    output_path = output_dir / "pilot_stats.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Required sample size: {sample_size}")
    
    return result

if __name__ == "__main__":
    main()
