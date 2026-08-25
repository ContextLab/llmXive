import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import json
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingest import (
    validate_icecube_data,
    validate_era5_data,
    log_exclusion_event,
    run_validation
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def valid_icecube_df():
    return pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'count': [100, 200, 150]
    })

@pytest.fixture
def invalid_icecube_df_negative():
    return pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02'],
        'count': [100, -50]
    })

@pytest.fixture
def invalid_icecube_df_missing_date():
    return pd.DataFrame({
        'timestamp': ['2023-01-01', '2023-01-02'],
        'count': [100, 200]
    })

@pytest.fixture
def valid_era5_df():
    return pd.DataFrame({
        'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'pressure': [1000, 500, 100],
        'temperature': [280, 250, 220]
    })

@pytest.fixture
def invalid_era5_df_pressure():
    return pd.DataFrame({
        'date': ['2023-01-01'],
        'pressure': [5.0],  # Below 10 hPa
        'temperature': [280]
    })

@pytest.fixture
def invalid_era5_df_temp():
    return pd.DataFrame({
        'date': ['2023-01-01'],
        'pressure': [500],
        'temperature': [100]  # Below 180 K
    })

def test_validate_icecube_data_valid(valid_icecube_df):
    assert validate_icecube_data(valid_icecube_df) is True

def test_validate_icecube_data_negative_counts(invalid_icecube_df_negative):
    assert validate_icecube_data(invalid_icecube_df_negative) is False

def test_validate_icecube_data_missing_date_column(invalid_icecube_df_missing_date):
    assert validate_icecube_data(invalid_icecube_df_missing_date) is False

def test_validate_era5_data_valid(valid_era5_df):
    assert validate_era5_data(valid_era5_df) is True

def test_validate_era5_data_out_of_range_pressure(invalid_era5_df_pressure):
    assert validate_era5_data(invalid_era5_df_pressure) is False

def test_validate_era5_data_out_of_range_temp(invalid_era5_df_temp):
    assert validate_era5_data(invalid_era5_df_temp) is False

def test_log_exclusion_event_creates_file(temp_dir):
    log_path = Path(temp_dir) / "test_alignment.json"
    log_exclusion_event("2023-01-01", "missing_era5", "era5", str(log_path))
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['date'] == "2023-01-01"
    assert data[0]['reason'] == "missing_era5"
    assert data[0]['source'] == "era5"

def test_log_exclusion_event_appends(temp_dir):
    log_path = Path(temp_dir) / "test_alignment.json"
    
    # First event
    log_exclusion_event("2023-01-01", "missing_era5", "era5", str(log_path))
    # Second event
    log_exclusion_event("2023-01-02", "missing_icecube", "icecube", str(log_path))
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['date'] == "2023-01-01"
    assert data[1]['date'] == "2023-01-02"

def test_run_validation_both_valid(valid_icecube_df, valid_era5_df):
    assert run_validation(valid_icecube_df, valid_era5_df) is True

def test_run_validation_one_invalid(valid_icecube_df, invalid_era5_df_pressure):
    assert run_validation(valid_icecube_df, invalid_era5_df_pressure) is False

def test_run_validation_both_invalid(invalid_icecube_df_negative, invalid_era5_df_pressure):
    assert run_validation(invalid_icecube_df_negative, invalid_era5_df_pressure) is False