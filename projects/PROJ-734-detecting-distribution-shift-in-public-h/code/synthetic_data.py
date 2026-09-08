"""
Synthetic data generator for unit tests ONLY.

This module generates synthetic public health surveillance data with controlled
anomalies for testing pipeline robustness. It is explicitly NOT used for the
final report or research analysis (see Constitution Principle VI and E-NO-DATA).

Generated data characteristics:
(a) Missing weeks (NaNs)
(b) Constant segments (zero variance)
(c) Outliers (extreme values)
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import os

# Ensure deterministic behavior for unit tests
DEFAULT_SEED = 42


def generate_synthetic_ili_series(
    n_weeks: int = 200,
    seed: int = DEFAULT_SEED,
    missing_rate: float = 0.05,
    constant_segment_prob: float = 0.1,
    outlier_rate: float = 0.02,
    base_mean: float = 2.0,
    base_std: float = 0.5
) -> pd.DataFrame:
    """
    Generate a synthetic ILI (Influenza-like Illness) time series with anomalies.

    Args:
        n_weeks: Total number of weeks to generate.
        seed: Random seed for reproducibility.
        missing_rate: Probability of a week being missing (NaN).
        constant_segment_prob: Probability of inserting a constant segment.
        outlier_rate: Probability of a value being an outlier.
        base_mean: Mean of the underlying normal distribution.
        base_std: Standard deviation of the underlying normal distribution.

    Returns:
        pd.DataFrame: A DataFrame with columns 'week_id', 'ili_value', and 'is_anomaly'.
    """
    rng = np.random.default_rng(seed)

    # Generate base time series
    weeks = np.arange(1, n_weeks + 1)
    ili_values = rng.normal(loc=base_mean, scale=base_std, size=n_weeks)

    # Track anomalies
    is_anomaly = np.zeros(n_weeks, dtype=bool)

    # 1. Inject Missing Weeks (NaNs)
    missing_mask = rng.random(n_weeks) < missing_rate
    ili_values[missing_mask] = np.nan
    is_anomaly[missing_mask] = True

    # 2. Inject Constant Segments (Zero Variance)
    # We iterate to find segments and force them to be constant
    # To avoid overlap with NaNs, we only modify non-NaN values
    valid_indices = np.where(~np.isnan(ili_values))[0]
    if len(valid_indices) > 10:
        # Pick a random start for a constant segment
        start_idx = rng.choice(valid_indices[:-10])
        length = rng.integers(5, 15)
        end_idx = min(start_idx + length, n_weeks)

        if end_idx > start_idx:
            # Ensure we don't overwrite NaNs in this range
            segment_mask = (np.arange(start_idx, end_idx) >= 0) & (np.arange(start_idx, end_idx) < n_weeks)
            segment_indices = np.arange(start_idx, end_idx)[segment_mask]
            segment_indices = segment_indices[~np.isnan(ili_values[segment_indices])]

            if len(segment_indices) > 1:
                constant_value = ili_values[segment_indices[0]]
                ili_values[segment_indices] = constant_value
                is_anomaly[segment_indices] = True

    # 3. Inject Outliers
    outlier_mask = rng.random(n_weeks) < outlier_rate
    # Outliers are extreme values (e.g., 10x the standard deviation)
    outlier_values = rng.uniform(low=base_mean + 5 * base_std, high=base_mean + 10 * base_std, size=np.sum(outlier_mask))
    ili_values[outlier_mask] = outlier_values
    is_anomaly[outlier_mask] = True

    df = pd.DataFrame({
        'week_id': weeks,
        'ili_value': ili_values,
        'is_anomaly': is_anomaly
    })

    return df


def save_synthetic_data(
    output_path: str,
    n_weeks: int = 200,
    seed: int = DEFAULT_SEED
) -> str:
    """
    Generate synthetic data and save it to a CSV file.

    Args:
        output_path: Path to save the CSV file.
        n_weeks: Number of weeks to generate.
        seed: Random seed.

    Returns:
        str: The path to the saved file.
    """
    df = generate_synthetic_ili_series(n_weeks=n_weeks, seed=seed)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)

    df.to_csv(output_path, index=False)
    return output_path


def main():
    """
    Main entry point for generating synthetic data via command line.
    Usage: python code/synthetic_data.py [output_path] [n_weeks] [seed]
    """
    import sys

    # Default parameters
    output_path = "data/raw/synthetic_ili.csv"
    n_weeks = 200
    seed = DEFAULT_SEED

    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    if len(sys.argv) > 2:
        n_weeks = int(sys.argv[2])
    if len(sys.argv) > 3:
        seed = int(sys.argv[3])

    saved_path = save_synthetic_data(output_path, n_weeks, seed)
    print(f"Synthetic data generated and saved to: {saved_path}")


if __name__ == "__main__":
    main()