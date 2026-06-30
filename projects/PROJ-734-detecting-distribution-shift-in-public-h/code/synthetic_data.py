"""
Synthetic data generator for unit tests only.

This module generates synthetic public health surveillance data with specific
pathological characteristics required for testing the distribution shift detection
pipeline. It is NOT to be used for final reports or real-world analysis.

Features generated:
(a) Missing weeks (NaNs)
(b) Constant segments (zero variance)
(c) Outliers

Reference: E-NO-DATA fallback mechanism ensures this data is never used
in production pipelines where real CDC data is required.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
import os

# Ensure reproducibility
DEFAULT_SEED = 42


def generate_synthetic_ili_series(
    n_weeks: int = 200,
    missing_rate: float = 0.05,
    constant_segment_len: int = 10,
    outlier_rate: float = 0.02,
    seed: Optional[int] = DEFAULT_SEED
) -> pd.DataFrame:
    """
    Generate a synthetic ILI (Influenza-like Illness) time series with
    controlled pathologies for unit testing.

    Parameters
    ----------
    n_weeks : int
        Total number of weeks to generate.
    missing_rate : float
        Proportion of weeks to set as NaN (missing data).
    constant_segment_len : int
        Length of the constant segment (zero variance) to inject.
    outlier_rate : float
        Proportion of non-NaN, non-constant values to replace with outliers.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: 'week', 'ili_percent', 'is_constant', 'is_outlier'.
        'ili_percent' contains the synthetic ILI values with injected pathologies.
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. Generate base realistic-looking ILI data
    # Simulate a seasonal pattern + some noise
    t = np.arange(n_weeks)
    # Seasonal component (annual cycle)
    seasonal = 2.0 + 1.5 * np.sin(2 * np.pi * t / 52)
    # Trend component (slight upward drift)
    trend = 0.005 * t
    # Random noise
    noise = np.random.normal(0, 0.3, n_weeks)

    ili_values = seasonal + trend + noise

    # Ensure values are positive and reasonable (ILI is a percentage)
    ili_values = np.clip(ili_values, 0.1, 10.0)

    # Create flags for tracking injected issues
    is_constant = np.zeros(n_weeks, dtype=bool)
    is_outlier = np.zeros(n_weeks, dtype=bool)

    # 2. Inject Constant Segment (Zero Variance)
    # Pick a random start index, ensuring it fits
    max_start = n_weeks - constant_segment_len - 10
    if max_start > 0:
        start_idx = np.random.randint(0, max_start)
        end_idx = start_idx + constant_segment_len
        constant_value = np.mean(ili_values[start_idx:end_idx])
        ili_values[start_idx:end_idx] = constant_value
        is_constant[start_idx:end_idx] = True

    # 3. Inject Outliers
    # Select indices that are not part of the constant segment and not already NaN
    n_outliers = int(n_weeks * outlier_rate)
    # Create a mask of valid indices (not constant)
    valid_indices = np.where(~is_constant)[0]
    if len(valid_indices) > n_outliers:
        outlier_indices = np.random.choice(valid_indices, n_outliers, replace=False)
        # Generate extreme values (e.g., 5x the median or very low)
        for idx in outlier_indices:
            if np.random.random() > 0.5:
                ili_values[idx] = np.median(ili_values) * 5.0
            else:
                ili_values[idx] = np.median(ili_values) * 0.1
        is_outlier[outlier_indices] = True

    # 4. Inject Missing Weeks (NaNs)
    # Select indices that are not part of the constant segment
    # (We want to test if the detector handles NaNs gracefully, but constant segments
    # are a specific edge case we want to preserve for testing)
    n_missing = int(n_weeks * missing_rate)
    # Avoid overwriting the constant segment with NaNs to keep that test case distinct
    # unless we specifically want to test that intersection. For now, keep them separate.
    available_indices = np.where(~is_constant)[0]
    if len(available_indices) > n_missing:
        missing_indices = np.random.choice(available_indices, n_missing, replace=False)
        ili_values[missing_indices] = np.nan
    elif len(available_indices) > 0:
        # Fallback if we don't have enough non-constant spots
        missing_indices = np.random.choice(available_indices, min(n_missing, len(available_indices)), replace=False)
        ili_values[missing_indices] = np.nan

    # Construct DataFrame
    df = pd.DataFrame({
        'week': t,
        'ili_percent': ili_values,
        'is_constant': is_constant,
        'is_outlier': is_outlier
    })

    # Add a fake 'year' and 'week_of_year' for realism if needed by downstream logic
    # Assuming start at week 1 of year 2020
    df['year'] = 2020 + (df['week'] // 52)
    df['week_of_year'] = (df['week'] % 52) + 1

    return df


def save_synthetic_data(
    output_path: str = "data/processed/synthetic_ili_test.csv",
    n_weeks: int = 200,
    missing_rate: float = 0.05,
    constant_segment_len: int = 10,
    outlier_rate: float = 0.02,
    seed: Optional[int] = DEFAULT_SEED
) -> str:
    """
    Generate synthetic data and save it to a CSV file.

    Parameters
    ----------
    output_path : str
        Path where the CSV file will be saved.
    n_weeks : int
        Number of weeks to generate.
    missing_rate : float
        Rate of missing data (NaNs).
    constant_segment_len : int
        Length of the constant segment.
    outlier_rate : float
        Rate of outliers.
    seed : int, optional
        Random seed.

    Returns
    -------
    str
        The absolute path of the saved file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = generate_synthetic_ili_series(
        n_weeks=n_weeks,
        missing_rate=missing_rate,
        constant_segment_len=constant_segment_len,
        outlier_rate=outlier_rate,
        seed=seed
    )

    df.to_csv(output_path, index=False)
    return os.path.abspath(output_path)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate synthetic ILI data for unit tests.")
    parser.add_argument("--output", type=str, default="data/processed/synthetic_ili_test.csv",
                        help="Output path for the CSV file.")
    parser.add_argument("--weeks", type=int, default=200, help="Number of weeks to generate.")
    parser.add_argument("--missing", type=float, default=0.05, help="Rate of missing data.")
    parser.add_argument("--constant", type=int, default=10, help="Length of constant segment.")
    parser.add_argument("--outliers", type=float, default=0.02, help="Rate of outliers.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")

    args = parser.parse_args()

    print(f"Generating synthetic data with seed={args.seed}...")
    path = save_synthetic_data(
        output_path=args.output,
        n_weeks=args.weeks,
        missing_rate=args.missing,
        constant_segment_len=args.constant,
        outlier_rate=args.outliers,
        seed=args.seed
    )

    # Log summary for verification
    df = pd.read_csv(path)
    stats = {
        "total_weeks": len(df),
        "missing_count": int(df['ili_percent'].isna().sum()),
        "constant_count": int(df['is_constant'].sum()),
        "outlier_count": int(df['is_outlier'].sum()),
        "file_path": path
    }

    print(json.dumps(stats, indent=2))
    print(f"Synthetic data saved to: {path}")
