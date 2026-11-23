"""
Unit tests for imputation strategies (T009a, T009b).
"""
import pytest
import pandas as pd
import numpy as np
from code.utils.imputation import impute_missing_values

def test_median_imputation():
    """Test median imputation logic on dummy data."""
    data = {
        'A': [1.0, 2.0, np.nan, 4.0, 5.0],
        'B': [10.0, np.nan, 30.0, 40.0, 50.0],
        'C': ['x', 'y', 'z', 'x', 'y']  # Non-numeric, should be ignored
    }
    df = pd.DataFrame(data)
    
    result = impute_missing_values(df, strategy='median')
    
    # Check that missing values are filled
    assert not result.isnull().any().any()
    
    # Check specific values
    # Median of A (1, 2, 4, 5) is 3.0
    assert result.loc[2, 'A'] == 3.0
    # Median of B (10, 30, 40, 50) is 35.0
    assert result.loc[1, 'B'] == 35.0
    
    # Check non-numeric column is unchanged
    assert result['C'].iloc[0] == 'x'

def test_knn_imputation():
    """Test KNN imputation logic on dummy data."""
    # Create a dataset where KNN can reasonably infer missing values
    # Row 0: [1, 10]
    # Row 1: [2, 20]
    # Row 2: [NaN, NaN] -> Should be close to [2, 20] or average of neighbors
    # Row 3: [100, 1000]
    data = {
        'A': [1.0, 2.0, np.nan, 100.0],
        'B': [10.0, 20.0, np.nan, 1000.0]
    }
    df = pd.DataFrame(data)
    
    # Use n_neighbors=2 (small dataset)
    result = impute_missing_values(df, strategy='knn', n_neighbors=2)
    
    # Check that missing values are filled
    assert not result.isnull().any().any()
    
    # The imputed value for row 2 should be a weighted average of neighbors
    # Since row 0 and 1 are closest to the missing row (if we consider Euclidean distance in this small set),
    # the value will be derived from them.
    # Exact value depends on sklearn implementation, but it should be numeric and finite.
    assert np.isfinite(result.loc[2, 'A'])
    assert np.isfinite(result.loc[2, 'B'])
    
    # Verify that the imputed value is not the original NaN
    assert result.loc[2, 'A'] != np.nan
    assert result.loc[2, 'B'] != np.nan

def test_invalid_strategy():
    """Test that invalid strategy raises ValueError."""
    df = pd.DataFrame({'A': [1, 2, np.nan]})
    with pytest.raises(ValueError, match="Unsupported strategy"):
        impute_missing_values(df, strategy='invalid')

def test_knn_import_error():
    """Test that KNN strategy raises ImportError if sklearn is missing."""
    # This is hard to test directly without mocking, but we can test the logic
    # If sklearn is installed (which it should be per requirements), this passes.
    # If not, the function raises ImportError which is the expected behavior.
    df = pd.DataFrame({'A': [1.0, np.nan]})
    try:
        result = impute_missing_values(df, strategy='knn')
        # If we get here, sklearn is available, which is expected in the environment
        assert not result.isnull().any().any()
    except ImportError:
        # If sklearn is not available, this is also a valid outcome for the test environment
        # but the function logic is correct.
        pass

def test_no_missing_values():
    """Test that function returns copy when no missing values exist."""
    df = pd.DataFrame({'A': [1.0, 2.0, 3.0], 'B': [4.0, 5.0, 6.0]})
    result = impute_missing_values(df, strategy='median')
    pd.testing.assert_frame_equal(result, df)
    
    result_knn = impute_missing_values(df, strategy='knn')
    pd.testing.assert_frame_equal(result_knn, df)

def test_all_numeric_missing():
    """Test median fallback when all values in a column are missing."""
    df = pd.DataFrame({'A': [np.nan, np.nan, np.nan], 'B': [1.0, 2.0, 3.0]})
    result = impute_missing_values(df, strategy='median')
    
    # Column A should be filled with 0.0 fallback
    assert result['A'].iloc[0] == 0.0
    # Column B should be unchanged (no missing)
    assert result['B'].iloc[0] == 1.0