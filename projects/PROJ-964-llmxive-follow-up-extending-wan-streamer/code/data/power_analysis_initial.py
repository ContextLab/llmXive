"""
T016a: Initial Sample Size Estimation (Theoretical)

Reads data/processed/filtered.parquet to compute empirical variance of
'latent_delta_magnitude'. If that file is missing, falls back to theoretical
defaults from data/metrics/theoretical_defaults.json.

Outputs: data/metrics/power_analysis_initial.json
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path for imports if needed
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Constants
FILTERED_PARQUET_PATH = PROJECT_ROOT / "data" / "processed" / "filtered.parquet"
THEORETICAL_DEFAULTS_PATH = PROJECT_ROOT / "data" / "metrics" / "theoretical_defaults.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "metrics" / "power_analysis_initial.json"

# Power analysis constants (standard defaults)
ALPHA = 0.05
POWER = 0.80

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_theoretical_defaults() -> dict:
    """
    Load theoretical defaults from JSON.
    Expects: {"variance": float, "effect_size": float}
    """
    if not THEORETICAL_DEFAULTS_PATH.exists():
        logger.warning(f"Theoretical defaults file not found at {THEORETICAL_DEFAULTS_PATH}. Using hardcoded fallbacks.")
        return {"variance": 0.05, "effect_size": 0.1}
    
    with open(THEORETICAL_DEFAULTS_PATH, 'r') as f:
        data = json.load(f)
    
    # Validate keys
    if 'variance' not in data or 'effect_size' not in data:
        logger.warning("Theoretical defaults missing 'variance' or 'effect_size'. Using hardcoded fallbacks.")
        return {"variance": 0.05, "effect_size": 0.1}
    
    return data

def calculate_sample_size(variance: float, effect_size: float) -> int:
    """
    Calculate minimum sample size for a two-sided t-test.
    Formula: n = 2 * ((Z_alpha + Z_beta) / delta)^2 * sigma^2
    where delta = effect_size (assuming standardized effect size or raw difference)
    and sigma^2 = variance.
    
    Note: If effect_size is a standardized Cohen's d, the formula simplifies to:
    n = 2 * ((Z_alpha + Z_beta) / d)^2
    
    Given the task description mentions "effect_size: 0.1" and "variance: 0.05",
    we treat these as raw parameters for a difference of means test where
    variance is the population variance sigma^2.
    
    Z_alpha for 0.05 (two-sided) ~ 1.96
    Z_beta for 0.80 power ~ 0.84
    """
    z_alpha = 1.96
    z_beta = 0.84
    
    if effect_size == 0:
        raise ValueError("Effect size cannot be zero for sample size calculation.")
    
    # n per group
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) * variance / (effect_size ** 2)
    
    # Total sample size
    total_n = int(np.ceil(n_per_group * 2))
    
    return max(total_n, 10) # Ensure at least 10 samples

def main():
    logger.info("Starting Initial Sample Size Estimation (Theoretical)...")
    
    variance = None
    effect_size = None
    variance_source = None
    
    # Step 1: Try to load empirical data
    if FILTERED_PARQUET_PATH.exists():
        logger.info(f"Found {FILTERED_PARQUET_PATH}. Computing empirical variance...")
        try:
            df = pd.read_parquet(FILTERED_PARQUET_PATH)
            if 'latent_delta_magnitude' not in df.columns:
                raise ValueError(f"Column 'latent_delta_magnitude' not found in {FILTERED_PARQUET_PATH}")
            
            # Compute variance, handling NaNs
            valid_values = df['latent_delta_magnitude'].dropna()
            if len(valid_values) < 2:
                raise ValueError("Not enough valid data points to compute variance.")
            
            variance = valid_values.var(ddof=1) # Sample variance
            effect_size = 0.1 # Default effect size for empirical run if not specified
            variance_source = "empirical"
            logger.info(f"Empirical variance computed: {variance:.6f}")
            
        except Exception as e:
            logger.error(f"Failed to compute empirical variance: {e}")
            logger.info("Falling back to theoretical defaults.")
            defaults = load_theoretical_defaults()
            variance = defaults['variance']
            effect_size = defaults['effect_size']
            variance_source = "theoretical"
    else:
        logger.info(f"File {FILTERED_PARQUET_PATH} not found. Using theoretical defaults.")
        defaults = load_theoretical_defaults()
        variance = defaults['variance']
        effect_size = defaults['effect_size']
        variance_source = "theoretical"
    
    # Step 2: Calculate sample size
    try:
        recommended_sample_size = calculate_sample_size(variance, effect_size)
    except ValueError as e:
        logger.error(f"Calculation failed: {e}")
        sys.exit(1)
    
    # Step 3: Prepare output
    result = {
        "recommended_sample_size": recommended_sample_size,
        "expected_variance": variance,
        "effect_size": effect_size,
        "variance_source": variance_source,
        "parameters": {
            "alpha": ALPHA,
            "power": POWER
        }
    }
    
    # Step 4: Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Successfully wrote results to {OUTPUT_PATH}")
    logger.info(f"Recommended sample size: {recommended_sample_size}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())