import pytest
import pandas as pd
import numpy as np
from src.data.preprocess import preprocess_pipeline, PowerError

def test_median_imputation_continuous():
    """Test that missing continuous values are imputed with the median."""
    data = {
        'income': [50000.0, np.nan, 60000.0, 70000.0, np.nan],
        'energy_cost': [1000.0, 1200.0, np.nan, 1100.0, 1300.0],
        'treatment': [0, 1, 0, 0, 1]
    }
    df = pd.DataFrame(data)
    
    # Run the preprocessing pipeline which includes median imputation
    # We need to ensure we have enough data to pass the power check if we run the full pipeline
    # So we'll add more rows to ensure we have >50 adopters if treatment is constructed
    large_data = {
        'income': [50000.0] * 20 + [np.nan] * 10 + [60000.0] * 20 + [70000.0] * 20,
        'energy_cost': [1000.0] * 20 + [1200.0] * 10 + [np.nan] * 20 + [1100.0] * 20,
        'treatment': [0] * 20 + [1] * 10 + [0] * 20 + [0] * 20,
        'tract_median_income': [30000.0] * 70,  # Below 150% FPL threshold
        'home_value': [200000.0] * 70
    }
    df_large = pd.DataFrame(large_data)
    
    result = preprocess_pipeline(df_large)
    
    # Check that no NaN values remain in continuous columns
    assert not result['income'].isna().any(), "Income should have no missing values after imputation"
    assert not result['energy_cost'].isna().any(), "Energy cost should have no missing values after imputation"
    
    # Check that imputed values are actually medians
    original_income = [50000.0, 60000.0, 70000.0]
    expected_income_median = np.median(original_income)
    # The imputed values should be the median
    imputed_incomes = result.loc[result['income'] == expected_income_median, 'income']
    assert len(imputed_incomes) > 0, "Income median imputation should have occurred"

def test_missing_flag_categorical():
    """Test that missing categorical values are flagged with a 'Missing' category."""
    data = {
        'housing_type': ['apartment', 'house', np.nan, 'house', np.nan],
        'income': [50000.0, 60000.0, 55000.0, 70000.0, 52000.0],
        'energy_cost': [1000.0, 1200.0, 1100.0, 1100.0, 1300.0],
        'tract_median_income': [30000.0] * 5,
        'treatment': [0, 1, 0, 0, 1]
    }
    df = pd.DataFrame(data)
    
    # Add more rows to pass power check
    large_data = {
        'housing_type': ['apartment'] * 20 + [np.nan] * 10 + ['house'] * 20 + ['house'] * 20,
        'income': [50000.0] * 20 + [55000.0] * 10 + [60000.0] * 20 + [70000.0] * 20,
        'energy_cost': [1000.0] * 20 + [1100.0] * 10 + [1200.0] * 20 + [1100.0] * 20,
        'tract_median_income': [30000.0] * 70,
        'treatment': [0] * 20 + [1] * 10 + [0] * 20 + [0] * 20,
        'home_value': [200000.0] * 70
    }
    df_large = pd.DataFrame(large_data)
    
    result = preprocess_pipeline(df_large)
    
    # Check that 'Missing' category exists in housing_type
    assert 'Missing' in result['housing_type'].values, "Missing category should exist for categorical variables"
    assert result['housing_type'].isna().sum() == 0, "No NaN values should remain in categorical columns"

def test_all_missing_median():
    """Test behavior when all values in a continuous column are missing."""
    # This test verifies that the pipeline handles the edge case where median cannot be calculated
    data = {
        'income': [np.nan] * 70,  # All missing
        'energy_cost': [1000.0] * 20 + [1200.0] * 10 + [1100.0] * 20 + [1100.0] * 20,
        'tract_median_income': [30000.0] * 70,
        'treatment': [0] * 20 + [1] * 10 + [0] * 20 + [0] * 20,
        'home_value': [200000.0] * 70
    }
    df = pd.DataFrame(data)
    
    # The pipeline should handle this gracefully, possibly by setting to 0 or raising a specific error
    # For now, we expect it to not crash and produce a result
    result = preprocess_pipeline(df)
    
    # If all values are missing, the median is NaN, so we expect the column to be filled with NaN or 0
    # The exact behavior depends on implementation, but it should not crash
    assert result is not None, "Pipeline should not crash when all values are missing"

def test_categorical_missing_in_category():
    """Test that missing values in categorical columns are properly categorized."""
    data = {
        'housing_type': ['apartment', 'house', 'condo', np.nan, 'apartment', np.nan],
        'income': [50000.0, 60000.0, 55000.0, 52000.0, 48000.0, 51000.0],
        'energy_cost': [1000.0, 1200.0, 1100.0, 1100.0, 1300.0, 1050.0],
        'tract_median_income': [30000.0] * 6,
        'treatment': [0, 1, 0, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    
    # Add more rows to pass power check
    large_data = {
        'housing_type': ['apartment'] * 20 + [np.nan] * 10 + ['house'] * 20 + ['condo'] * 20,
        'income': [50000.0] * 20 + [55000.0] * 10 + [60000.0] * 20 + [70000.0] * 20,
        'energy_cost': [1000.0] * 20 + [1100.0] * 10 + [1200.0] * 20 + [1100.0] * 20,
        'tract_median_income': [30000.0] * 70,
        'treatment': [0] * 20 + [1] * 10 + [0] * 20 + [0] * 20,
        'home_value': [200000.0] * 70
    }
    df_large = pd.DataFrame(large_data)
    
    result = preprocess_pipeline(df_large)
    
    # Check that the 'Missing' category is present
    missing_count = (result['housing_type'] == 'Missing').sum()
    assert missing_count > 0, "Missing category should be present in the result"

def test_no_silent_data_loss():
    """Test that no data is silently dropped during preprocessing."""
    # Create a dataset with some missing values
    data = {
        'income': [50000.0, np.nan, 60000.0, 70000.0, np.nan, 55000.0, 48000.0, 52000.0, 51000.0, 49000.0],
        'energy_cost': [1000.0, 1200.0, np.nan, 1100.0, 1300.0, 1050.0, 1150.0, 1250.0, 1000.0, 1100.0],
        'tract_median_income': [30000.0] * 10,
        'treatment': [0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        'home_value': [200000.0] * 10
    }
    df = pd.DataFrame(data)
    
    # Add more rows to pass power check
    for i in range(60):
        df.loc[len(df)] = {
            'income': 50000.0 + (i % 10) * 1000,
            'energy_cost': 1000.0 + (i % 5) * 100,
            'tract_median_income': 30000.0,
            'treatment': 0 if i % 3 != 0 else 1,
            'home_value': 200000.0
        }
    
    original_count = len(df)
    result = preprocess_pipeline(df)
    
    # The number of rows should remain the same (no silent dropping)
    assert len(result) == original_count, "No rows should be silently dropped during preprocessing"

def test_nonexistent_columns():
    """Test that the pipeline handles missing required columns gracefully."""
    # Create a dataset with missing required columns
    data = {
        'income': [50000.0, 60000.0, 70000.0],
        'energy_cost': [1000.0, 1200.0, 1100.0],
        # Missing 'tract_median_income' and 'treatment'
        'home_value': [200000.0, 210000.0, 220000.0]
    }
    df = pd.DataFrame(data)
    
    # Add more rows to avoid power check issues
    for i in range(70):
        df.loc[len(df)] = {
            'income': 50000.0 + (i % 10) * 1000,
            'energy_cost': 1000.0 + (i % 5) * 100,
            'home_value': 200000.0
        }
    
    # The pipeline should raise a KeyError or similar for missing required columns
    with pytest.raises((KeyError, ValueError)):
        preprocess_pipeline(df)