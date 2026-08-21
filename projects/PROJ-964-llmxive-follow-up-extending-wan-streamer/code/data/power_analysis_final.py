"""
Final Power Analysis (T017)

Re-runs power analysis using the sampled dataset to confirm the final sample size
satisfies power requirements (FR-016, SC-008).

Reads:
  - data/processed/sampled_dataset.parquet
  - data/metrics/power_analysis_initial.json (for baseline parameters)

Writes:
  - data/metrics/power_analysis_final.json
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Ensure we can import from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from scipy import stats

# Import config to get paths/constants if needed
try:
    from config import get_config_summary
except ImportError:
    # Fallback if config isn't in path yet
    get_config_summary = lambda: {}

logger = logging.getLogger(__name__)

def load_sampled_dataset(path: Path) -> pd.DataFrame:
    """Load the sampled dataset parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Sampled dataset not found at {path}")
    logger.info(f"Loading sampled dataset from {path}")
    return pd.read_parquet(path)

def load_initial_power_analysis(path: Path) -> dict:
    """Load the initial power analysis results."""
    if not path.exists():
        raise FileNotFoundError(f"Initial power analysis not found at {path}")
    logger.info(f"Loading initial power analysis from {path}")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_empirical_variance(df: pd.DataFrame, column: str = 'latent_delta_magnitude') -> float:
    """Calculate empirical variance from the sampled data."""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataframe. Available: {df.columns.tolist()}")
    
    values = df[column].dropna()
    if len(values) < 2:
        raise ValueError(f"Insufficient data points to calculate variance for '{column}'")
    
    variance = values.var(ddof=1)
    logger.info(f"Empirical variance for '{column}': {variance:.6f}")
    return float(variance)

def calculate_effect_size(initial_variance: float, empirical_variance: float) -> float:
    """
    Calculate effect size based on variance change.
    Using Cohen's d approximation for variance differences.
    """
    if empirical_variance <= 0 or initial_variance <= 0:
        return 0.0
    
    # Effect size as standardized difference
    pooled_std = np.sqrt((initial_variance + empirical_variance) / 2)
    # Using the ratio of variances as a proxy for effect magnitude
    if pooled_std == 0:
        return 0.0
    
    # Normalized difference
    effect_size = abs(empirical_variance - initial_variance) / pooled_std
    return float(effect_size)

def run_power_analysis(
    variance: float,
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    test_type: str = 'two_sample'
) -> int:
    """
    Calculate required sample size using power analysis.
    Uses statsmodels or scipy approximation.
    """
    # For two-sample t-test (or similar), using standard formula
    # n = 2 * (Z_alpha + Z_beta)^2 * sigma^2 / delta^2
    # where delta = effect_size * sigma
    
    z_alpha = stats.norm.ppf(1 - alpha / 2)  # Two-tailed
    z_beta = stats.norm.ppf(power)
    
    if effect_size == 0:
        # If no effect, return a large number or max limit
        return 100000
    
    # Simplified: n per group
    n_per_group = 2 * ((z_alpha + z_beta) ** 2) / (effect_size ** 2)
    
    total_n = int(np.ceil(n_per_group * 2))  # Total for two groups
    
    # Ensure minimum sample size
    min_sample = 5000
    if total_n < min_sample:
        total_n = min_sample
    
    logger.info(f"Calculated required sample size: {total_n}")
    return total_n

def main():
    parser = argparse.ArgumentParser(description="Final Power Analysis")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/sampled_dataset.parquet"),
        help="Path to sampled dataset parquet file"
    )
    parser.add_argument(
        "--initial",
        type=Path,
        default=Path("data/metrics/power_analysis_initial.json"),
        help="Path to initial power analysis JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/metrics/power_analysis_final.json"),
        help="Path to output final power analysis JSON"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load data
        df = load_sampled_dataset(args.input)
        initial_analysis = load_initial_power_analysis(args.initial)

        # Get initial parameters
        initial_variance = initial_analysis.get("expected_variance", 0.05)
        initial_effect_size = initial_analysis.get("effect_size", 0.1)

        # Calculate empirical values
        empirical_variance = calculate_empirical_variance(df, "latent_delta_magnitude")
        
        # Recalculate effect size based on empirical variance
        # If initial analysis had a specific effect size target, we compare against that
        # Otherwise, we derive from the variance change
        if "recommended_sample_size" in initial_analysis:
            # Use the target effect size from initial analysis if available
            effect_size = initial_effect_size
        else:
            effect_size = calculate_effect_size(initial_variance, empirical_variance)

        # Run final power analysis
        final_sample_size = run_power_analysis(
            variance=empirical_variance,
            effect_size=effect_size
        )

        # Check if current sample size is sufficient
        current_sample_size = len(df)
        is_sufficient = current_sample_size >= final_sample_size

        # Prepare output
        output_data = {
            "recommended_sample_size": final_sample_size,
            "current_sample_size": current_sample_size,
            "is_sufficient": is_sufficient,
            "expected_variance": empirical_variance,
            "effect_size": effect_size,
            "variance_source": "empirical",
            "alpha": 0.05,
            "power": 0.80,
            "satisfied_requirements": is_sufficient
        }

        # Write output
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Final power analysis written to {args.output}")
        logger.info(f"Sample size sufficient: {is_sufficient} (current: {current_sample_size}, required: {final_sample_size})")

        # Exit with appropriate code
        if not is_sufficient:
            logger.warning("Current sample size is below recommended. Consider collecting more data.")
            # Do not exit with error - this is informational for the researcher
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())