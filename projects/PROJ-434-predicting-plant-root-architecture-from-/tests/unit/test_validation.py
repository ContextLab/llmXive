"""
Unit tests for the validation module (T015).

Tests cover:
- Match proportion calculation
- Row filtering logic
- Data quality error raising
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import logging
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.validation import (
    calculate_match_proportion,
    filter_valid_rows,
    validate_soil_data_coverage,
    SOIL_PREDICTORS
)
from utils.exceptions import DataQualityError
from ingestion.logging_utils import setup_logging, get_logger

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with mixed valid/invalid soil data."""
    return pd.DataFrame({
        'record_id': ['1', '2', '3', '4', '5'],
        'latitude': [45.0, 46.0, 47.0, 48.0, 49.0],
        'longitude': [-122.0, -123.0, -124.0, -125.0, -126.0],
        'species_name': ['A', 'B', 'C', 'D', 'E'],
        'soil_n': [10.0, np.nan, 12.0, 11.0, 13.0],
        'soil_p': [5.0, 6.0, np.nan, 5.5, 6.0],
        'soil_k': [200.0, 210.0, 205.0, np.nan, 215.0],
        'soil_ph': [6.5, 6.8, 6.7, 6.6, 6.9]
    })

@pytest.fixture
def clean_logs():
    """Ensure log directories are clean for testing."""
    log_dir = Path("data/logs")
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after test
    if log_dir.exists():
        shutil.rmtree(log_dir)

@pytest.fixture
def setup_logger(clean_logs):
    """Setup a test logger."""
    log_file = Path("data/logs/test_validation.log")
    setup_logging(str(log_file))
    return get_logger(__name__)

def test_calculate_match_proportion_all_valid():
    """Test with all rows having valid soil data."""
    df = pd.DataFrame({
        'soil_n': [1.0, 2.0, 3.0],
        'soil_p': [1.0, 2.0, 3.0],
        'soil_k': [1.0, 2.0, 3.0],
        'soil_ph': [1.0, 2.0, 3.0]
    })
    prop = calculate_match_proportion(df, ['soil_n', 'soil_p', 'soil_k', 'soil_ph'])
    assert prop == 1.0

def test_calculate_match_proportion_all_invalid():
    """Test with all rows having missing soil data."""
    df = pd.DataFrame({
        'soil_n': [np.nan, 2.0, np.nan],
        'soil_p': [1.0, np.nan, np.nan],
        'soil_k': [np.nan, np.nan, np.nan],
        'soil_ph': [np.nan, np.nan, np.nan]
    })
    prop = calculate_match_proportion(df, ['soil_n', 'soil_p', 'soil_k', 'soil_ph'])
    assert prop == 0.0

def test_calculate_match_proportion_partial_valid(sample_df):
    """Test with mixed valid/invalid rows."""
    # In sample_df:
    # Row 0: all valid
    # Row 1: missing soil_n
    # Row 2: missing soil_p
    # Row 3: missing soil_k
    # Row 4: all valid
    # Expected: 2/5 = 0.4
    prop = calculate_match_proportion(sample_df, SOIL_PREDICTORS)
    assert prop == 0.4

def test_calculate_match_proportion_empty_df():
    """Test with empty DataFrame."""
    df = pd.DataFrame(columns=['soil_n', 'soil_p'])
    prop = calculate_match_proportion(df, ['soil_n', 'soil_p'])
    assert prop == 0.0

def test_filter_valid_rows_removes_invalid(sample_df):
    """Test that filter_valid_rows removes rows with missing data."""
    valid_df, excluded = filter_valid_rows(sample_df, SOIL_PREDICTORS)
    
    # Should keep 2 rows (indices 0 and 4)
    assert len(valid_df) == 2
    assert list(valid_df['record_id']) == ['1', '5']
    
    # Should exclude 3 rows
    assert len(excluded) == 3
    
    # Check excluded reasons
    excluded_ids = [e['record_id'] for e in excluded]
    assert '2' in excluded_ids
    assert '3' in excluded_ids
    assert '4' in excluded_ids

def test_filter_valid_rows_logs_exclusions(sample_df, setup_logger, clean_logs):
    """Test that excluded rows are logged."""
    logger = setup_logger
    valid_df, excluded = filter_valid_rows(sample_df, SOIL_PREDICTORS)
    
    # Check that exclusion log file was created
    log_file = Path("data/logs/record_exclusions.log")
    assert log_file.exists()
    
    # Verify content
    with open(log_file, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 3  # 3 excluded rows

def test_validate_soil_data_coverage_pass():
    """Test validation passes when proportion >= threshold."""
    df = pd.DataFrame({
        'soil_n': [1.0, 2.0, 3.0, 4.0, 5.0],
        'soil_p': [1.0, 2.0, 3.0, 4.0, 5.0],
        'soil_k': [1.0, 2.0, 3.0, 4.0, 5.0],
        'soil_ph': [1.0, 2.0, 3.0, 4.0, 5.0]
    })
    
    # 100% valid, should pass with 0.90 threshold
    prop = validate_soil_data_coverage(df, SOIL_PREDICTORS, threshold=0.90)
    assert prop == 1.0

def test_validate_soil_data_coverage_fail(sample_df, setup_logger, clean_logs):
    """Test validation fails when proportion < threshold."""
    logger = setup_logger
    
    # 40% valid, should fail with 0.90 threshold
    with pytest.raises(DataQualityError) as exc_info:
        validate_soil_data_coverage(sample_df, SOIL_PREDICTORS, threshold=0.90)
    
    assert exc_info.value.match_proportion == 0.4
    assert "Match proportion" in str(exc_info.value)
    
    # Check error log
    log_file = Path("data/logs/validation_error.log")
    assert log_file.exists()

def test_validate_soil_data_coverage_custom_threshold():
    """Test with a lower threshold that passes."""
    df = pd.DataFrame({
        'soil_n': [1.0, np.nan, 3.0, np.nan, 5.0],
        'soil_p': [1.0, 2.0, np.nan, 4.0, 5.0],
        'soil_k': [1.0, 2.0, 3.0, 4.0, np.nan],
        'soil_ph': [1.0, 2.0, 3.0, 4.0, 5.0]
    })
    # 2/5 = 0.4 valid
    # With threshold 0.3, should pass
    prop = validate_soil_data_coverage(df, SOIL_PREDICTORS, threshold=0.3)
    assert prop == 0.4
    assert prop >= 0.3
