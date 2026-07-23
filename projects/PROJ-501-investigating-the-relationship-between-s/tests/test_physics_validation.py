"""
Unit tests for physics validation logic (T026).
"""
import pytest
import pandas as np
import pandas as pd
import numpy as np
from physics import validate_derived_columns

def test_validate_no_nan():
    """Test validation passes when no NaNs are present."""
    df = pd.DataFrame({
        'cumulative_flux': [1.0, 2.0, 3.0],
        'mass_loss_rate': [1e10, 2e10, 3e10],
        'retention_fraction': [0.9, 0.8, 0.7]
    })
    assert validate_derived_columns(df) is True

def test_validate_nan_raises():
    """Test validation raises ValueError when NaNs are present."""
    df = pd.DataFrame({
        'cumulative_flux': [1.0, np.nan, 3.0],
        'mass_loss_rate': [1e10, 2e10, 3e10],
        'retention_fraction': [0.9, 0.8, 0.7]
    })
    with pytest.raises(ValueError, match="NaN values detected"):
        validate_derived_columns(df)

def test_validate_missing_column_raises():
    """Test validation raises ValueError if a required column is missing."""
    df = pd.DataFrame({
        'cumulative_flux': [1.0, 2.0, 3.0],
        'mass_loss_rate': [1e10, 2e10, 3e10]
        # retention_fraction missing
    })
    with pytest.raises(ValueError, match="Missing required derived columns"):
        validate_derived_columns(df)