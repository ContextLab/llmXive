"""
Unit tests for data completeness validation logic (T016a).
"""
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import json

# Import the function to test
from code.data_validation import validate_data_completeness, REQUIRED_VARIABLES

@pytest.fixture
def sample_real_data():
    """Create a valid dataframe with real data characteristics."""
    data = {col: [1.0] * 100 for col in REQUIRED_VARIABLES}
    # Add some noise but keep it complete
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def sample_incomplete_real_data():
    """Create a dataframe with < 95% completeness for real data."""
    data = {col: [1.0] * 100 for col in REQUIRED_VARIABLES}
    # Introduce 10% missing values in a critical column
    df = pd.DataFrame(data)
    df.loc[:9, 'home_era'] = np.nan  # 10 missing out of 100 = 90% completeness
    return df

@pytest.fixture
def sample_synthetic_data():
    """Create a synthetic dataframe that is incomplete."""
    data = {col: [1.0] * 100 for col in REQUIRED_VARIABLES}
    df = pd.DataFrame(data)
    df.loc[:10, 'away_runs'] = np.nan  # 11 missing out of 100 = 89% completeness
    return df

def test_validate_real_data_passes(sample_real_data):
    """Real data with >95% completeness should pass."""
    result = validate_data_completeness(sample_real_data, is_real_data=True, threshold=0.95)
    assert result['threshold_met'] is True
    assert result['overall_completeness'] == 1.0
    assert 'Empirical Hypothesis Untested' not in result['flags']

def test_validate_real_data_fails_and_raises(sample_incomplete_real_data):
    """Real data with <95% completeness should raise ValueError."""
    with pytest.raises(ValueError, match="Data completeness"):
        validate_data_completeness(sample_incomplete_real_data, is_real_data=True, threshold=0.95)

def test_validate_synthetic_data_flags(sample_synthetic_data):
    """Synthetic data with low completeness should pass validation but set the flag."""
    result = validate_data_completeness(sample_synthetic_data, is_real_data=False, threshold=0.95)
    assert result['threshold_met'] is False
    assert result['is_real_data'] is False
    assert 'Empirical Hypothesis Untested' in result['flags']

def test_missing_columns_raises():
    """Validation should fail immediately if required columns are missing."""
    df = pd.DataFrame({'game_id': [1, 2, 3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_data_completeness(df, is_real_data=True)

def test_completeness_calculation():
    """Test specific completeness calculation logic."""
    data = {
        'game_id': [1, 2, 3, 4],
        'home_era': [1.0, 1.0, np.nan, 1.0],
        'away_era': [1.0, 1.0, 1.0, 1.0]
    }
    df = pd.DataFrame(data)
    # Required vars subset for test
    result = validate_data_completeness(
        df, 
        is_real_data=False, 
        required_vars=['game_id', 'home_era', 'away_era'],
        threshold=0.95
    )
    
    # game_id: 4/4, home_era: 3/4, away_era: 4/4
    # Total cells: 12, Missing: 1. Completeness: 11/12 = 0.9166
    assert abs(result['overall_completeness'] - (11/12)) < 0.001
    assert result['column_stats']['home_era']['non_null'] == 3
    assert result['column_stats']['home_era']['ratio'] == 0.75