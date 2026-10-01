import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Import configuration from code/setup_pytest.py
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_pytest import (
    sample_fraction, 
    stratify_column, 
    cpu_only, 
    temp_data_dir, 
    temp_results_dir,
    setup_test_environment,
    sample_data_loader,
    cpu_only_mode
)

@pytest.fixture(scope="session", autouse=True)
def global_test_config():
    """
    Global fixture to set up test environment based on setup_pytest.py config.
    """
    # Ensure temp directories exist
    Path(temp_data_dir).mkdir(parents=True, exist_ok=True)
    Path(temp_results_dir).mkdir(parents=True, exist_ok=True)
    
    # Enforce CPU-only if configured
    if cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    yield {
        "temp_data_dir": temp_data_dir,
        "temp_results_dir": temp_results_dir,
        "sample_fraction": sample_fraction,
        "stratify_column": stratify_column,
        "cpu_only": cpu_only
    }
    
    # Cleanup
    for d in [temp_data_dir, temp_results_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)

@pytest.fixture
def mock_moral_machine_data(global_test_config):
    """
    Generate a small mock Moral Machine dataset for testing ingestion logic.
    Uses real column names but synthetic values for speed.
    """
    n_rows = 100
    data = {
        "participant_id": [f"P{i}" for i in range(n_rows)],
        "latitude": np.random.uniform(-60, 60, n_rows),
        "longitude": np.random.uniform(-180, 180, n_rows),
        "timestamp": pd.date_range("2016-01-01", periods=n_rows, freq="h"),
        "response_time": np.random.uniform(200, 5000, n_rows),
        "country": np.random.choice(["US", "UK", "DE", "FR", "JP"], n_rows),
        "dilemma_id": np.random.choice(["D1", "D2", "D3"], n_rows)
    }
    df = pd.DataFrame(data)
    save_path = Path(global_test_config["temp_data_dir"]) / "mock_moral_machine.csv"
    df.to_csv(save_path, index=False)
    return save_path

@pytest.fixture
def mock_era5_data(global_test_config):
    """
    Generate a small mock ERA5 dataset for testing matching logic.
    """
    n_rows = 50
    data = {
        "grid_id": [f"G{i//10}" for i in range(n_rows)],
        "timestamp": pd.date_range("2016-01-01", periods=n_rows, freq="h"),
        "latitude": np.random.uniform(-60, 60, n_rows),
        "longitude": np.random.uniform(-180, 180, n_rows),
        "temperature_celsius": np.random.uniform(-10, 35, n_rows)
    }
    df = pd.DataFrame(data)
    save_path = Path(global_test_config["temp_data_dir"]) / "mock_era5.csv"
    df.to_csv(save_path, index=False)
    return save_path

@pytest.fixture
def stratified_sample_fixture(sample_data_loader, mock_moral_machine_data):
    """
    Fixture providing a stratified sample of the mock data.
    """
    df = pd.read_csv(mock_moral_machine_data)
    return sample_data_loader(df)

@pytest.fixture(autouse=True)
def enforce_cpu_only():
    """
    Ensure every test runs in CPU-only mode unless explicitly marked otherwise.
    """
    if os.getenv("PYTEST_CPU_ONLY", "true").lower() in ("true", "1", "yes"):
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    yield
    # Reset if needed (handled by global config cleanup)

def pytest_report_header(config):
    """
    Add custom header to test reports.
    """
    return [
        "Test Configuration:",
        f"  CPU-Only: {os.getenv('CUDA_VISIBLE_DEVICES', 'Not Set') == ''}",
        f"  Sample Fraction: {config.getoption('--sample-fraction')}",
        f"  Stratify Column: {config.getoption('--stratify-column')}",
    ]
