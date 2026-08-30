import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data_validation import validate_data_completeness, REQUIRED_VARIABLES

def create_test_dataframe(completeness_rate=1.0, missing_cols=None):
    """Helper to create a test DataFrame with specific completeness."""
    n_rows = 100
    data = {}
    
    # Create all required columns
    for col in REQUIRED_VARIABLES:
        if missing_cols and col in missing_cols:
            # Entire column missing (simulated by not adding it to df later)
            data[col] = [None] * n_rows
        else:
            # Fill with value or NaN based on rate
            if completeness_rate == 1.0:
                data[col] = np.random.rand(n_rows) if col not in ['game_id', 'team_id', 'opponent_id'] else range(n_rows)
            else:
                # Randomly set some to NaN
                mask = np.random.random(n_rows) < completeness_rate
                values = np.where(mask, np.random.rand(n_rows), np.nan)
                if col in ['game_id', 'team_id', 'opponent_id']:
                    values = np.where(mask, range(n_rows), np.nan)
                data[col] = values
    
    df = pd.DataFrame(data)
    # If columns were marked as missing, drop them entirely
    if missing_cols:
        df = df.drop(columns=[c for c in missing_cols if c in df.columns])
        
    return df

def test_completeness_above_threshold_real_data():
    """Test that high completeness passes for real data."""
    df = create_test_dataframe(completeness_rate=0.98)
    is_valid, completeness, status = validate_data_completeness(df, is_real_data=True)
    
    assert is_valid is True
    assert status == "Valid"
    assert completeness['hits'] > 0.95

def test_completeness_below_threshold_real_data_raises():
    """Test that low completeness raises ValueError for real data."""
    df = create_test_dataframe(completeness_rate=0.80)
    
    with pytest.raises(ValueError) as excinfo:
        validate_data_completeness(df, is_real_data=True, threshold=0.95)
    
    assert "below threshold" in str(excinfo.value).lower()

def test_completeness_below_threshold_synthetic_data():
    """Test that low completeness returns False and flags synthetic mode."""
    df = create_test_dataframe(completeness_rate=0.80)
    
    is_valid, completeness, status = validate_data_completeness(df, is_real_data=False, threshold=0.95)
    
    assert is_valid is False
    assert status == "Empirical Hypothesis Untested"

def test_missing_columns_real_data_raises():
    """Test that missing required columns raises ValueError for real data."""
    df = create_test_dataframe(missing_cols=['hits'])
    
    with pytest.raises(ValueError) as excinfo:
        validate_data_completeness(df, is_real_data=True)
    
    assert "Missing required columns" in str(excinfo.value)

def test_empty_dataframe_real_data_raises():
    """Test that empty DataFrame raises ValueError for real data."""
    df = pd.DataFrame()
    
    with pytest.raises(ValueError) as excinfo:
        validate_data_completeness(df, is_real_data=True)
    
    assert "empty" in str(excinfo.value).lower()
