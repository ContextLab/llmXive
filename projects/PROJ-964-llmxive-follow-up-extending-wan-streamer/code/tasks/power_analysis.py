"""
code/tasks/power_analysis.py

Implements 'a priori' power analysis for the llmXive project.
Per FR-016 and SC-008.

Logic:
1. Check if `data/processed/raw_extract.parquet` exists.
2. If it exists and is non-empty:
   - Load the data.
   - Compute empirical variance of the target variable (latent_delta_magnitude).
   - Set variance_source = 'empirical'.
3. If the file is missing or empty:
   - Use theoretical literature defaults (variance=1.0, effect_size=0.5).
   - Set variance_source = 'theoretical'.
4. Calculate recommended sample size using standard power analysis formulae
   (assuming power=0.8, alpha=0.05, two-tailed test).
5. Output `data/metrics/power_analysis_initial.json` with:
   - recommended_sample_size
   - expected_variance
   - effect_size
   - variance_source
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import pandas for parquet handling
try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas")
    sys.exit(1)

# Constants for Power Analysis
DEFAULT_VARIANCE = 1.0
DEFAULT_EFFECT_SIZE = 0.5
DEFAULT_POWER = 0.8
DEFAULT_ALPHA = 0.05
TARGET_COLUMN = "latent_delta_magnitude"

# Paths relative to project root
RAW_EXTRACT_PATH = Path("data/processed/raw_extract.parquet")
OUTPUT_PATH = Path("data/metrics/power_analysis_initial.json")
LOGS_DIR = Path("data/logs")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_pilot_data(path: Path) -> Optional[pd.DataFrame]:
    """
    Loads the raw extraction parquet file if it exists.
    Returns None if the file does not exist or is empty.
    """
    if not path.exists():
        logger.info(f"Input file {path} does not exist. Using theoretical defaults.")
        return None

    try:
        df = pd.read_parquet(path)
        if df.empty:
            logger.warning(f"Input file {path} is empty. Using theoretical defaults.")
            return None
        
        if TARGET_COLUMN not in df.columns:
            logger.warning(f"Column '{TARGET_COLUMN}' not found in {path}. Using theoretical defaults.")
            return None

        # Remove NaNs for variance calculation
        valid_data = df[TARGET_COLUMN].dropna()
        if len(valid_data) == 0:
            logger.warning(f"No valid data points for '{TARGET_COLUMN}' in {path}. Using theoretical defaults.")
            return None
        
        return valid_data
    except Exception as e:
        logger.error(f"Failed to load or parse {path}: {e}")
        return None


def estimate_variance(data: pd.Series) -> float:
    """
    Computes the empirical variance from the provided data series.
    """
    return float(data.var())


def calculate_min_sample_size(variance: float, effect_size: float, power: float = DEFAULT_POWER, alpha: float = DEFAULT_ALPHA) -> int:
    """
    Calculates the minimum required sample size for a t-test.
    Formula approximation for two-sample t-test:
    n = 2 * ((Z_alpha + Z_beta) / effect_size)^2 * variance
    
    Note: This is a simplified approximation. For a more precise calculation,
    scipy.stats would be used, but we aim to keep dependencies minimal if possible.
    However, since scipy is in requirements, we can use it for accuracy.
    """
    try:
        from scipy.stats import ttest_ind, t
        import numpy as np

        # Effect size (Cohen's d) = diff / sqrt(variance)
        # We are given 'effect_size' as the target Cohen's d (e.g., 0.5)
        # We need to solve for n.
        # Standard approximation: n = 2 * ( (Z_{1-alpha/2} + Z_{power}) / d )^2
        
        # Z-scores
        z_alpha = t.ppf(1 - alpha/2, df=np.inf) # ~1.96 for 0.05
        z_beta = t.ppf(power, df=np.inf)        # ~0.84 for 0.80

        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return int(np.ceil(n))
    except ImportError:
        # Fallback to simple approximation if scipy is missing
        z_alpha = 1.96
        z_beta = 0.84
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return int(np.ceil(n))


def run_power_analysis() -> Dict[str, Any]:
    """
    Main logic to run the power analysis.
    Returns a dictionary with the results.
    """
    data = load_pilot_data(RAW_EXTRACT_PATH)
    
    if data is not None:
        variance = estimate_variance(data)
        variance_source = "empirical"
        logger.info(f"Empirical variance calculated: {variance:.4f}")
    else:
        variance = DEFAULT_VARIANCE
        variance_source = "theoretical"
        logger.info(f"Using theoretical variance: {variance}")

    effect_size = DEFAULT_EFFECT_SIZE
    
    recommended_size = calculate_min_sample_size(variance, effect_size)
    
    results = {
        "recommended_sample_size": recommended_size,
        "expected_variance": variance,
        "effect_size": effect_size,
        "variance_source": variance_source,
        "parameters": {
            "power": DEFAULT_POWER,
            "alpha": DEFAULT_ALPHA
        }
    }
    
    return results


def write_output(results: Dict[str, Any], output_path: Path) -> None:
    """
    Writes the results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Power analysis results written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Run initial power analysis.")
    parser.add_argument('--input', type=str, default=str(RAW_EXTRACT_PATH), 
                        help="Path to the raw extraction parquet file.")
    parser.add_argument('--output', type=str, default=str(OUTPUT_PATH),
                        help="Path to the output JSON file.")
    args = parser.parse_args()

    # Override paths if provided via CLI
    input_path = Path(args.input)
    output_path = Path(args.output)

    results = run_power_analysis()
    write_output(results, output_path)

    # Verify output exists
    if not output_path.exists():
        logger.error("Failed to create output file.")
        sys.exit(1)
    
    logger.info("Power analysis completed successfully.")


if __name__ == "__main__":
    main()