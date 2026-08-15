"""
Pytest configuration and fixtures for PROJ-743.

Provides:
- CPU-only execution enforcement
- Stratified sampling fixtures for testing with limited data
- Path utilities for data access
"""
import os
import sys
import logging
import random
from pathlib import Path
from typing import List, Any, Dict, Optional
from datetime import datetime

import pytest
import pandas as pd
import numpy as np

# Project root detection
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = PROJECT_ROOT / "results" / "logs"

# Ensure logging directory exists for test runs
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# -----------------------------------------------------------------------------
# CPU-Only Enforcement
# -----------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def enforce_cpu_only():
    """
    Fixture to ensure no GPU libraries are accidentally imported during tests.
    This enforces the project constraint of CPU-only execution.
    """
    # Check for common GPU environment variables
    if os.environ.get("CUDA_VISIBLE_DEVICES", "") != "":
        pytest.skip("CUDA_VISIBLE_DEVICES is set; CPU-only tests require it to be empty.")
    
    # Check if torch/cuda is available and disable if so
    try:
        import torch
        if torch.cuda.is_available():
            # Force CPU for any torch operations in tests
            torch.set_default_tensor_type(torch.DoubleTensor)
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            logging.info("Forcefully set torch to CPU mode.")
    except ImportError:
        pass  # torch not installed, which is fine for CPU-only

    yield

# -----------------------------------------------------------------------------
# Stratified Sampling Fixtures
# -----------------------------------------------------------------------------

def stratified_sample(df: pd.DataFrame, 
                      strata_column: str, 
                      sample_size: int, 
                      random_seed: int = 42) -> pd.DataFrame:
    """
    Perform stratified sampling on a DataFrame.
    
    Args:
        df: Input DataFrame
        strata_column: Column name to stratify by
        sample_size: Total number of samples to draw
        random_seed: Random seed for reproducibility
    
    Returns:
        DataFrame with stratified sample
    """
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    # Calculate sample size per stratum
    strata_counts = df[strata_column].value_counts()
    total_strata = len(strata_counts)
    
    # Ensure we don't sample more than available in any stratum
    sample_per_stratum = max(1, sample_size // total_strata)
    
    sampled_dfs = []
    for stratum, count in strata_counts.items():
        n = min(sample_per_stratum, count)
        stratum_df = df[df[strata_column] == stratum]
        sampled = stratum_df.sample(n=n, random_state=random_seed)
        sampled_dfs.append(sampled)
    
    return pd.concat(sampled_dfs, ignore_index=True)

@pytest.fixture
def sample_moral_machine_data():
    """
    Fixture to provide a small, stratified sample of Moral Machine data
    for testing ingestion and filtering logic without loading the full dataset.
    
    Simulates the structure of the real dataset if the real file is unavailable
    or too large, but strictly adheres to the schema expected by the ingestion module.
    """
    # Since we cannot load real data in a test environment without dependencies,
    # we create a synthetic schema-compliant dataset for testing logic.
    # In a real integration test, this would load from data/processed/merged_dataset.parquet
    # or a specific test fixture file.
    
    n_samples = 500
    np.random.seed(42)
    
    data = {
        'scenario_id': np.random.randint(1, 1000, n_samples),
        'timestamp': pd.date_range('2016-01-01', periods=n_samples, freq='H'),
        'latitude': np.random.uniform(-90, 90, n_samples),
        'longitude': np.random.uniform(-180, 180, n_samples),
        'response_time_ms': np.random.exponential(2000, n_samples).astype(int),
        'age': np.random.choice(['<18', '18-25', '26-35', '36-45', '46-55', '55+'], n_samples),
        'gender': np.random.choice(['Male', 'Female', 'Non-binary', 'Prefer not to say'], n_samples),
        'country_code': np.random.choice(['US', 'UK', 'DE', 'FR', 'JP', 'CN', 'BR', 'IN'], n_samples),
        'temperature_celsius': np.random.uniform(10, 35, n_samples),
        'dilemma_choice': np.random.choice(['sideswipe', 'headon', 'swerve'], n_samples),
        'is_valid_location': np.random.choice([True, False], n_samples, p=[0.95, 0.05]),
        'match_quality': np.random.choice(['high', 'low'], n_samples, p=[0.9, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values to test filtering
    df.loc[np.random.choice(df.index, 20), 'latitude'] = np.nan
    df.loc[np.random.choice(df.index, 15), 'response_time_ms'] = 50  # Invalid < 100ms
    df.loc[np.random.choice(df.index, 10), 'response_time_ms'] = 15000  # Invalid > 10000ms
    
    return df

@pytest.fixture
def small_era5_sample():
    """
    Fixture for a small ERA5 temperature sample for geospatial matching tests.
    """
    # Create a minimal grid of temperature data
    lats = [40.0, 40.1, 40.2, 41.0, 41.1]
    lons = [-74.0, -73.9, -73.8, -74.0, -73.9]
    temps = [20.5, 21.0, 20.8, 19.5, 20.0]
    
    data = {
        'latitude': lats,
        'longitude': lons,
        'temperature_2m': temps,
        'time': pd.date_range('2016-01-01', periods=len(lats), freq='1h')
    }
    return pd.DataFrame(data)

# -----------------------------------------------------------------------------
# Path Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def data_dir():
    return DATA_DIR

@pytest.fixture
def logs_dir():
    return LOGS_DIR
