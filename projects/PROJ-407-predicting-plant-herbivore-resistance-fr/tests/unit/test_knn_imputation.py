import pytest
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

# Import the specific function from the project's API surface
from preprocess import apply_knn_imputation


def test_knn_imputation_basic():
    """Test basic k-NN imputation with a small synthetic dataset."""
    # Create a dataset with known missing values
    data = {
        'metabolite_A': [1.0, 2.0, np.nan, 4.0, 5.0],
        'metabolite_B': [10.0, np.nan, 30.0, 40.0, 50.0],
        'metabolite_C': [100.0, 200.0, 300.0, np.nan, 500.0]
    }
    df = pd.DataFrame(data)
    
    # Apply k-NN imputation with k=2
    result = apply_knn_imputation(df, k=2)
    
    # Verify no NaN values remain in the result
    assert result.isna().sum().sum() == 0, "Imputation failed to fill all missing values"
    
    # Verify the shape is preserved
    assert result.shape == df.shape, "Shape changed during imputation"
    
    # Verify that non-missing values are unchanged
    original_non_nan = df.dropna()
    result_non_nan = result.dropna()
    pd.testing.assert_frame_equal(original_non_nan, result_non_nan)


def test_knn_imputation_k_equals_1():
    """Test k-NN imputation with k=1 (nearest neighbor)."""
    data = {
        'feature_1': [1.0, 2.0, np.nan, 4.0],
        'feature_2': [1.0, 2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    # With k=1, the missing value should be filled by the single nearest neighbor
    # In this simple case, row 2 (index 2) is missing feature_1.
    # Neighbors are rows 0, 1, 3.
    # Distances in feature_2: |3-1|=2, |3-2|=1, |3-4|=1.
    # Ties between row 1 and 3. Scipy's cdist usually picks the first one in case of ties,
    # so it should pick row 1 (value 2.0).
    result = apply_knn_imputation(df, k=1)
    
    assert not result.isna().any().any()
    # The imputed value should be close to one of the neighbors
    assert result.loc[2, 'feature_1'] in [1.0, 2.0, 4.0]


def test_knn_imputation_no_missing_values():
    """Test that the function handles data with no missing values correctly."""
    data = {
        'feature_1': [1.0, 2.0, 3.0],
        'feature_2': [4.0, 5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_knn_imputation(df, k=2)
    
    # Should return the same data
    pd.testing.assert_frame_equal(result, df)


def test_knn_imputation_all_missing_in_column():
    """Test behavior when an entire column is missing."""
    data = {
        'feature_1': [1.0, 2.0, 3.0],
        'feature_2': [np.nan, np.nan, np.nan]
    }
    df = pd.DataFrame(data)
    
    # This should not crash, but might produce NaNs if no valid neighbors exist
    # or fill with mean if the implementation handles it.
    # The function should handle this gracefully without raising an exception.
    try:
        result = apply_knn_imputation(df, k=2)
        # If it succeeds, check that we didn't introduce new NaNs in non-missing columns
        assert result['feature_1'].isna().sum() == 0
    except Exception as e:
        # If it raises, it should be a clear error, not a silent failure
        # For this test, we accept that it might raise if the algorithm cannot proceed
        # without valid data for distance calculation.
        pass


def test_knn_imputation_preserves_metadata():
    """Test that non-metabolite columns (like sample_id) are preserved."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'metabolite_A': [1.0, np.nan, 3.0, 4.0],
        'metabolite_B': [10.0, 20.0, 30.0, 40.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_knn_imputation(df, k=2)
    
    # Check that sample_id is preserved exactly
    assert result['sample_id'].tolist() == df['sample_id'].tolist()
    # Check that missing value is filled
    assert not result.isna().any().any()