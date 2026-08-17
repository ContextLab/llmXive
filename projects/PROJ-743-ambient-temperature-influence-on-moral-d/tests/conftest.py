"""
Pytest configuration and fixtures for the Ambient Temperature Influence on Moral Decision Speed project.

This module configures:
- CPU-only execution (disabling any potential GPU usage)
- Stratified sampling utilities for memory-constrained environments
- Custom markers for test categorization
- Fixtures for common test data loading
"""

import os
import sys
import pytest
import random
import numpy as np
import pandas as pd
from pathlib import Path

# Force CPU-only execution
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # Suppress TensorFlow GPU warnings

# Project root configuration
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Stratified sampling configuration
STRATIFIED_SAMPLE_SIZE = 1000  # Default sample size for stratified testing
RANDOM_SEED = 42  # Fixed seed for reproducibility


def pytest_configure(config):
    """Configure custom markers and environment settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "cpu_only: explicitly mark test as CPU-only (enforces no GPU)"
    )
    config.addinivalue_line(
        "markers", "stratified: mark test to use stratified sampling on large datasets"
    )


@pytest.fixture(scope="session", autouse=True)
def enforce_cpu_only():
    """Ensure all tests run on CPU only."""
    # Double-check environment variables
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "GPU devices must be disabled"
    yield


@pytest.fixture
def stratified_sample_data(request, tmp_path):
    """
    Fixture to generate stratified sample data for testing.
    
    This fixture creates a synthetic dataset that mimics the structure of the
    merged Moral Machine + ERA5 dataset, then applies stratified sampling.
    
    Usage:
        def test_my_function(stratified_sample_data):
            df = stratified_sample_data
            # Run tests on stratified sample
    """
    # Get sample size from request or use default
    sample_size = request.param if hasattr(request, 'param') else STRATIFIED_SAMPLE_SIZE
    
    # Create a realistic mock dataset structure
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)
    
    n_total = min(sample_size * 10, 5000)  # Create a larger dataset to sample from
    
    # Generate stratified data based on key variables
    # Stratify by: temperature_range (cold, moderate, hot) and dilemma_complexity
    temperatures = np.random.normal(20, 8, n_total)  # Mean 20°C, std 8°C
    complexities = np.random.choice(['simple', 'complex'], n_total, p=[0.6, 0.4])
    
    # Create temperature ranges for stratification
    def get_temp_range(temp):
        if temp < 15:
            return 'cold'
        elif temp < 25:
            return 'moderate'
        else:
            return 'hot'
    
    temp_ranges = [get_temp_range(t) for t in temperatures]
    
    # Generate response times (log-normal distribution to mimic real data)
    response_times = np.random.lognormal(mean=4.5, sigma=0.8, size=n_total)
    
    # Generate other necessary columns
    dilemma_choices = np.random.choice(['save_occupants', 'save_pedestrians'], n_total)
    participant_ids = [f"participant_{i}" for i in range(n_total)]
    country_codes = np.random.choice(['US', 'GB', 'DE', 'FR', 'JP', 'BR', 'IN'], n_total)
    
    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'temperature_celsius': temperatures,
        'response_time_ms': response_times,
        'dilemma_complexity': complexities,
        'dilemma_choice': dilemma_choices,
        'country_code': country_codes,
        'temp_range': temp_ranges
    })
    
    # Apply stratified sampling
    strata = ['temp_range', 'dilemma_complexity']
    sample_df = df.groupby(strata, group_keys=False).apply(
        lambda x: x.sample(n=min(int(sample_size / len(df.groupby(strata).groups)), len(x)), random_state=RANDOM_SEED)
    ).reset_index(drop=True)
    
    # Ensure we have the requested sample size
    if len(sample_df) > sample_size:
        sample_df = sample_df.sample(n=sample_size, random_state=RANDOM_SEED)
    
    return sample_df


@pytest.fixture
def small_moral_machine_sample(tmp_path):
    """
    Fixture providing a small, known subset of Moral Machine data for testing.
    
    This creates a minimal CSV file that mimics the structure of the real Moral
    Machine dataset, suitable for quick unit tests.
    """
    data = {
        'session_id': ['s1', 's2', 's3', 's4', 's5'],
        'participant_id': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'timestamp': ['2016-03-15 10:30:00', '2016-03-15 11:45:00', '2016-03-16 09:15:00', '2016-03-16 14:20:00', '2016-03-17 16:50:00'],
        'latitude': [51.5074, 48.8566, 52.5200, 35.6762, 40.7128],
        'longitude': [-0.1278, 2.3522, 13.4050, 139.6503, -74.0060],
        'response_time_ms': [2500, 3200, 1800, 4100, 2900],
        'choice': ['save_occupants', 'save_pedestrians', 'save_occupants', 'save_pedestrians', 'save_occupants'],
        'dilemma_type': ['pedestrians_vs_occupants', 'pedestrians_vs_occupants', 'pedestrians_vs_occupants', 'pedestrians_vs_occupants', 'pedestrians_vs_occupants'],
        'country': ['GB', 'FR', 'DE', 'JP', 'US']
    }
    
    df = pd.DataFrame(data)
    file_path = tmp_path / "moral_machine_sample.csv"
    df.to_csv(file_path, index=False)
    
    return file_path


@pytest.fixture
def small_era5_sample(tmp_path):
    """
    Fixture providing a small ERA5 temperature sample for testing.
    
    This creates a minimal Parquet file mimicking the structure of ERA5 data.
    """
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2016-01-01', end='2016-01-07', freq='H')
    n_hours = len(dates)
    
    data = {
        'datetime': dates,
        'latitude': [51.5074] * n_hours,
        'longitude': [-0.1278] * n_hours,
        'temperature_2m': [10.5 + np.sin(i / 24) * 3 for i in range(n_hours)]  # Simulate daily cycle
    }
    
    df = pd.DataFrame(data)
    file_path = tmp_path / "era5_sample.parquet"
    df.to_parquet(file_path, index=False)
    
    return file_path


@pytest.fixture(autouse=True)
def reset_random_seeds():
    """Reset random seeds before each test for reproducibility."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    pd.random.seed(RANDOM_SEED) if hasattr(pd, 'random') else None
    yield
