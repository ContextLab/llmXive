"""
Pytest configuration and fixtures for the Ambient Temperature Influence on Moral Decision Speed project.

This module provides:
- CPU-only execution enforcement
- Stratified sampling fixtures for memory-constrained testing
- Common test utilities
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Generator, Dict, Any

# Ensure CPU-only execution by setting environment variables
@pytest.fixture(autouse=True)
def enforce_cpu_only():
    """Force all computations to use CPU only."""
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TF warnings
    yield
    # Cleanup if needed

def stratified_sample(
    df: pd.DataFrame,
    stratify_col: str,
    sample_size: Optional[int] = None,
    fraction: Optional[float] = None,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Perform stratified sampling on a DataFrame.

    Args:
        df: Input DataFrame
        stratify_col: Column name to stratify by
        sample_size: Number of samples to draw (mutually exclusive with fraction)
        fraction: Fraction of samples to draw (mutually exclusive with sample_size)
        random_state: Random seed for reproducibility

    Returns:
        Stratified sample DataFrame

    Raises:
        ValueError: If neither sample_size nor fraction is provided, or if both are provided
    """
    if sample_size is None and fraction is None:
        raise ValueError("Either sample_size or fraction must be provided")
    if sample_size is not None and fraction is not None:
        raise ValueError("Only one of sample_size or fraction should be provided")

    # Set random seed for reproducibility
    np.random.seed(random_state)

    # Perform stratified sampling
    if sample_size is not None:
        # Calculate fraction based on total size
        fraction = sample_size / len(df)

    sample = df.groupby(stratify_col, group_keys=False).apply(
        lambda x: x.sample(frac=fraction, random_state=random_state)
    )

    return sample.reset_index(drop=True)

@pytest.fixture
def sample_moral_machine_data() -> pd.DataFrame:
    """
    Fixture providing a stratified sample of Moral Machine data for testing.
    Uses stratification by country and dilemma type to ensure representative sampling.
    """
    # This fixture assumes the full dataset is available at data/raw/moral_machine.parquet
    # For testing purposes, we create a synthetic sample that mimics the structure
    # In production, this would load from the real data file

    # Create a minimal synthetic dataset for testing
    np.random.seed(42)
    n_samples = 1000

    data = {
        'timestamp': pd.date_range('2016-01-01', periods=n_samples, freq='1min'),
        'country': np.random.choice(['US', 'UK', 'DE', 'FR', 'JP', 'BR', 'IN'], n_samples),
        'dilemma_type': np.random.choice(['pedestrian_vs_passenger', 'young_vs_old', 'healthy_vs_unhealthy'], n_samples),
        'response_time_ms': np.random.exponential(2000, n_samples).clip(100, 10000),
        'latitude': np.random.uniform(-90, 90, n_samples),
        'longitude': np.random.uniform(-180, 180, n_samples),
        'temperature_celsius': np.random.normal(20, 8, n_samples),
        'choice': np.random.choice([0, 1], n_samples)
    }

    df = pd.DataFrame(data)

    # Apply stratified sampling (10% sample)
    sampled_df = stratified_sample(df, stratify_col='country', fraction=0.1, random_state=42)

    return sampled_df

@pytest.fixture
def sample_era5_data() -> pd.DataFrame:
    """
    Fixture providing a sample of ERA5 temperature data for testing.
    """
    # Create a minimal synthetic ERA5 dataset for testing
    np.random.seed(42)
    n_points = 500

    data = {
        'time': pd.date_range('2016-01-01', periods=n_points, freq='1h'),
        'latitude': np.random.uniform(30, 60, n_points),
        'longitude': np.random.uniform(-10, 30, n_points),
        'temperature_2m': np.random.normal(15, 10, n_points)
    }

    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Fixture providing a temporary output directory for test artifacts.
    Ensures tests don't pollute the actual results/ directory.
    """
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup is handled by pytest's tmp_path fixture
