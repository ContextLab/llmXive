"""
Unit test for NaN handling in descriptor computation.

This test verifies that NaN values are handled according to the 
project's deterministic logic: >5% missing -> drop record, else impute.
"""
import pytest
import pandas as pd
import numpy as np
from typing import List, Tuple
from utils.logging_config import get_logger

logger = get_logger(__name__)

def _apply_nan_logic(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Apply the deterministic NaN handling logic to a DataFrame.
    
    Logic:
    1. Calculate NaN ratio per column.
    2. If NaN ratio > threshold (5%), drop ALL rows that have NaN in that column.
    3. If NaN ratio <= threshold, impute NaNs in that column with the column's median.
    
    Args:
        df: Input DataFrame.
        threshold: Ratio threshold (default 0.05).
        
    Returns:
        Processed DataFrame.
    """
    result = df.copy()
    total_rows = len(result)
    
    if total_rows == 0:
        return result

    for col in result.columns:
        if col == 'target':
            continue
            
        nan_count = result[col].isna().sum()
        nan_ratio = nan_count / total_rows
        
        if nan_ratio > threshold:
            # Drop rows with NaN in this column
            mask = result[col].notna()
            result = result[mask]
            logger.debug(f"Dropped {total_rows - len(result)} rows due to NaN in {col} (ratio={nan_ratio:.2f} > {threshold})")
        else:
            # Impute with median
            median_val = result[col].median()
            if pd.isna(median_val):
                # If all values are NaN, fill with 0.0 as fallback
                median_val = 0.0
            result[col] = result[col].fillna(median_val)
            logger.debug(f"Imputed NaN in {col} with median={median_val} (ratio={nan_ratio:.2f} <= {threshold})")
            
    return result

def test_nan_handling_logic_drop():
    """
    Test the deterministic NaN handling logic when >5% NaNs exist.
    Rows with NaN should be dropped.
    """
    # Create test data with NaN values where >5% of rows are affected
    # 1 NaN out of 5 = 20% > 5% -> Drop rows
    data = {
        'descriptor_1': [1.0, 2.0, np.nan, 4.0, 5.0],  # 20% NaN -> Drop rows with NaN
        'descriptor_2': [1.0, 2.0, 3.0, 4.0, 5.0],     # 0% NaN
        'target': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    result = _apply_nan_logic(df, threshold=0.05)
    
    # Row index 2 has NaN in descriptor_1, so it should be dropped
    # Expected indices: 0, 1, 3, 4
    expected_indices = [0, 1, 3, 4]
    
    assert list(result.index) == expected_indices, f"Expected indices {expected_indices}, got {list(result.index)}"
    assert len(result) == 4
    assert not result['descriptor_1'].isna().any()

def test_nan_handling_logic_impute():
    """
    Test median imputation for columns with <=5% NaN.
    """
    # 1 NaN out of 100 = 1% <= 5% -> Impute
    data = {
        'descriptor_1': [1.0] * 99 + [np.nan], 
        'descriptor_2': [2.0] * 100,
        'target': [10.0] * 100
    }
    df = pd.DataFrame(data)
    
    result = _apply_nan_logic(df, threshold=0.05)
    
    # No rows should be dropped
    assert len(result) == 100
    
    # The NaN should be imputed with the median (which is 1.0)
    assert result['descriptor_1'].iloc[-1] == 1.0
    assert not result['descriptor_1'].isna().any()

def test_mixed_nan_handling():
    """
    Test a scenario with mixed NaN ratios across columns.
    """
    data = {
        'desc_high_nan': [1.0, np.nan, 3.0, 4.0, np.nan], # 2/5 = 40% -> Drop
        'desc_low_nan': [1.0, 2.0, np.nan, 4.0, 5.0],     # 1/5 = 20% -> Drop (Wait, 20% > 5%, so drop)
        'desc_ok': [1.0, 2.0, 3.0, 4.0, 5.0],             # 0% -> Keep
        'target': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    # Let's adjust to make one column <= 5%
    # 1 NaN out of 20 rows = 5%
    data = {
        'desc_high_nan': [1.0, np.nan, 3.0, 4.0, np.nan], # 2/5 = 40% -> Drop rows with NaN
        'desc_ok': [1.0, 2.0, 3.0, 4.0, 5.0],             # 0%
        'target': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    result = _apply_nan_logic(df, threshold=0.05)
    
    # Row 1 and 4 have NaN in desc_high_nan, so they are dropped.
    # Remaining indices: 0, 2, 3
    expected_indices = [0, 2, 3]
    assert list(result.index) == expected_indices

def test_median_imputation_calculation():
    """
    Verify the median calculation used for imputation.
    """
    data = {
        'desc': [1.0, 2.0, 3.0, 4.0, np.nan],
        'target': [10.0, 20.0, 30.0, 40.0, 50.0]
    }
    df = pd.DataFrame(data)
    
    # Manually calculate median for [1, 2, 3, 4] -> 2.5
    median_val = df['desc'].median()
    assert median_val == 2.5
    
    # Apply logic (1/5 = 20% > 5%, so it drops, not imputes)
    # To test imputation, we need < 5%
    data_impute = {
        'desc': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, np.nan], # 1/10 = 10% > 5% still
        'target': list(range(10))
    }
    # 1/20 = 5%
    data_impute = {
        'desc': [float(i) for i in range(19)] + [np.nan],
        'target': list(range(20))
    }
    df_impute = pd.DataFrame(data_impute)
    result = _apply_nan_logic(df_impute, threshold=0.05)
    
    # Median of 0..18 is 9.0
    assert result['desc'].iloc[-1] == 9.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])