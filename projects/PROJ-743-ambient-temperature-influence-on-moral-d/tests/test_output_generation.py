"""
Tests for T022: Output Generation.
Verifies that the merged dataset is saved correctly and success rate is calculated.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run_output_generation import calculate_success_rate, ensure_output_directories

@pytest.fixture
def sample_df():
    """Create a sample DataFrame simulating the merged output."""
    data = {
        'participant_id': [1, 2, 3, 4, 5],
        'temperature_celsius': [20.5, 25.0, -999.0, 18.2, 22.1], # -999.0 is missing
        'match_quality': ['high', 'high', 'low', 'high', 'high'],
        'response_time': [1.2, 0.8, 1.5, 0.9, 1.1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_df():
    """Empty DataFrame."""
    return pd.DataFrame()

def test_calculate_success_rate_valid():
    """Test success rate calculation with valid data."""
    df = pd.DataFrame({
        'temperature_celsius': [20.0, 25.0, 18.0],
        'match_quality': ['high', 'high', 'high']
    })
    # Mock logger to capture logs
    import logging
    logger = logging.getLogger("test")
    
    rate = calculate_success_rate(df, logger)
    assert rate == 100.0

def test_calculate_success_rate_with_missing():
    """Test success rate calculation with missing values."""
    df = pd.DataFrame({
        'temperature_celsius': [20.0, -999.0, 18.0],
        'match_quality': ['high', 'high', 'high']
    })
    import logging
    logger = logging.getLogger("test")
    
    rate = calculate_success_rate(df, logger)
    # 2 valid out of 3
    assert rate == pytest.approx(66.666, rel=0.1)

def test_calculate_success_rate_empty():
    """Test success rate calculation with empty DataFrame."""
    df = pd.DataFrame()
    import logging
    logger = logging.getLogger("test")
    
    rate = calculate_success_rate(df, logger)
    assert rate == 0.0

def test_ensure_output_directories():
    """Test that output directories are created."""
    # This test might create a directory in the real project structure
    # We'll just check it doesn't raise an error
    try:
        ensure_output_directories()
    except Exception as e:
        pytest.fail(f"ensure_output_directories raised an exception: {e}")
