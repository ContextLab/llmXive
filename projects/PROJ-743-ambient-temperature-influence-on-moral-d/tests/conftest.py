"""
Pytest configuration for CPU-only execution and stratified sampling.
"""
import os
import sys
import random
from pathlib import Path
from typing import List, Any, Dict, Optional

import pytest
import pandas as pd
import numpy as np

# Add project root to path to ensure imports work when running from tests/
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path_env_override


def pytest_configure(config):
    """
    Configure pytest at startup.
    - Enforce CPU-only execution for ML/Stats libraries if applicable.
    - Register custom markers for stratified sampling.
    """
    # Force CPU-only for torch/tensorflow if they were imported (defensive)
    # Note: This project uses statsmodels/pandas, but we set env vars for consistency
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"

    # Register markers
    config.addinivalue_line(
        "markers", "stratified: Mark a test to use stratified sampling on the input data."
    )
    config.addinivalue_line(
        "markers", "cpu_only: Explicitly mark a test as CPU-only (enforced via config)."
    )


@pytest.fixture(scope="session", autouse=True)
def enforce_cpu_only():
    """
    Session-scoped fixture that ensures the environment is set to CPU-only.
    This is an autouse fixture, so it runs for every test.
    """
    # Re-assert environment variables to ensure no library overrides them
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    yield
    # No teardown needed for env vars usually, but we could restore if needed


@pytest.fixture
def stratified_sample(request):
    """
    Fixture to perform stratified sampling on a DataFrame based on a column.
    Usage:
      @pytest.mark.stratified(column='country', n=50)
      def test_my_model(stratified_sample):
          df = stratified_sample(...)
    """

    def _sample(df: pd.DataFrame, column: str, n_per_strata: int = 10) -> pd.DataFrame:
        if column not in df.columns:
            raise ValueError(f"Stratification column '{column}' not found in DataFrame.")

        if len(df) == 0:
            return df

        groups = df.groupby(column)
        sampled_dfs = []

        for name, group in groups:
            if len(group) <= n_per_strata:
                sampled_dfs.append(group)
            else:
                sampled_dfs.append(group.sample(n=n_per_strata, random_state=42))

        return pd.concat(sampled_dfs, ignore_index=True)

    return _sample


@pytest.fixture
def mock_data_loader():
    """
    Fixture to provide a mock data loader for testing ingestion logic.
    Returns a DataFrame with realistic but synthetic structure (not values).
    """
    # We use a small, deterministic dataset for unit tests.
    # This is NOT the real data source, but a structural mock.
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'latitude': [51.5074, 40.7128, 35.6895, -33.8688, 55.7558],
        'longitude': [-0.1278, -74.0060, 139.6917, 151.2093, 37.6173],
        'timestamp': pd.to_datetime(['2016-01-01 12:00:00', '2016-01-02 14:30:00',
                                     '2016-01-03 09:15:00', '2016-01-04 18:45:00',
                                     '2016-01-05 11:20:00']),
        'response_time': [2500, 1800, 3200, 4100, 2900],
        'country': ['UK', 'USA', 'Japan', 'Australia', 'Russia'],
        'dilemma_id': ['D1', 'D1', 'D2', 'D2', 'D3']
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Fixture to create a temporary output directory structure mimicking the project.
    """
    dirs = [
        "data/processed",
        "results/logs",
        "results/figures",
        "results/stats"
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path
