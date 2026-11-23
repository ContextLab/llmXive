"""
Unit tests for the data ingestion module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import filter_missing_data, cap_outliers, impute_covariates

def test_filter_missing_data():
    """Test that rows with missing values are correctly filtered."""
    df = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'value': [10.0, np.nan, 30.0, 40.0]
    })
    result = filter_missing_data(df, ['value'])
    assert len(result) == 3
    assert result['value'].isnull().sum() == 0

def test_cap_outliers():
    """Test that outliers are capped at percentiles."""
    df = pd.DataFrame({
        'value': [1, 2, 3, 4, 100]  # 100 is an outlier
    })
    # Cap at 10th and 90th percentiles
    # 10th of [1,2,3,4,100] is approx 1.6, 90th is approx 38.8
    result = cap_outliers(df, 'value', 10, 90)
    max_val = result['value'].max()
    assert max_val < 100
    assert max_val <= 40 # Allow some tolerance

def test_impute_covariates():
    """Test that missing numeric values are filled with median."""
    df = pd.DataFrame({
        'numeric': [1.0, 2.0, np.nan, 4.0],
        'categorical': ['A', 'B', np.nan, 'A']
    })
    result = impute_covariates(df)
    assert result['numeric'].isnull().sum() == 0
    assert result['categorical'].isnull().sum() == 0
    # Check median imputation for numeric (median of 1,2,4 is 2)
    assert result.loc[2, 'numeric'] == 2.0
    # Check mode imputation for categorical (mode is A)
    assert result.loc[2, 'categorical'] == 'A'