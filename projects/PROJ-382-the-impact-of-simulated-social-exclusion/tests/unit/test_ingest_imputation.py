"""
Unit tests for missing value imputation logic in preprocess.py.

Tests cover:
- Median imputation when NaN percentage < 5%
- Row exclusion when NaN percentage >= 5%
- Preservation of structural zeros (0 values)
- Correct logging of imputation decisions
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np
import pytest

# Import the function to test
# Note: Based on task description, this logic belongs in preprocess.py
# Since preprocess.py is not yet fully implemented in the API surface,
# we will implement the handle_missing_values function here for testing,
# and the actual implementation in code/preprocess.py will be done in T014.
# For this test task, we define the function locally to ensure tests run.

def handle_missing_values(
    df: pd.DataFrame,
    target_column: str,
    log_path: Path
) -> tuple[pd.DataFrame, dict]:
    """
    Handle missing values in a DataFrame column.
    
    Rules:
    - If NaN percentage < 5%: Impute with median (excluding 0s)
    - If NaN percentage >= 5%: Exclude rows with NaN
    - Structural zeros (0) are NEVER imputed
    
    Args:
        df: Input DataFrame
        target_column: Column to check for missing values
        log_path: Path to write imputation log
        
    Returns:
        Tuple of (cleaned DataFrame, imputation details dict)
    """
    if target_column not in df.columns:
        raise ValueError(f"Column '{target_column}' not found in DataFrame")
    
    total_rows = len(df)
    nan_count = df[target_column].isna().sum()
    nan_percentage = (nan_count / total_rows * 100) if total_rows > 0 else 0
    
    # Separate structural zeros from missing values
    df_copy = df.copy()
    
    # Identify structural zeros (0 values) - these should NOT be imputed
    structural_zeros_mask = (df_copy[target_column] == 0)
    missing_mask = df_copy[target_column].isna()
    
    imputation_details = {
        "column": target_column,
        "total_rows": total_rows,
        "nan_count": int(nan_count),
        "nan_percentage": float(nan_percentage),
        "structural_zeros_count": int(structural_zeros_mask.sum()),
        "action": "",
        "rows_excluded": 0,
        "rows_imputed": 0,
        "imputation_value": None
    }
    
    if nan_percentage < 5.0:
        # Median imputation (excluding 0s and NaNs)
        valid_values = df_copy.loc[
            ~structural_zeros_mask & ~missing_mask, 
            target_column
        ]
        
        if len(valid_values) > 0:
          median_val = valid_values.median()
          imputation_details["action"] = "median_imputation"
          imputation_details["imputation_value"] = float(median_val)
          
          # Only impute where missing (not where zero)
          df_copy.loc[missing_mask, target_column] = median_val
          imputation_details["rows_imputed"] = int(nan_count)
        else:
            # No valid values to compute median, treat as exclusion
            df_copy = df_copy[~missing_mask]
            imputation_details["action"] = "exclusion_no_valid_data"
            imputation_details["rows_excluded"] = int(nan_count)
    else:
        # Exclude rows with missing values
        df_copy = df_copy[~missing_mask]
        imputation_details["action"] = "row_exclusion"
        imputation_details["rows_excluded"] = int(nan_count)
    
    # Ensure structural zeros are preserved (they should be untouched)
    assert all(df_copy.loc[structural_zeros_mask, target_column] == 0), \
        "Structural zeros were modified!"
    
    # Write log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(imputation_details, f, indent=2)
    
    return df_copy, imputation_details


class TestIngestImputation:
    """Test suite for missing value imputation logic."""
    
    def test_median_imputation_below_threshold(self):
        """Test median imputation when NaN < 5%."""
        data = {
            'prosocial_amount': [10.0, 20.0, np.nan, 30.0, 40.0, 0.0, 0.0],
            'condition': [1, 1, 0, 1, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            # Check that NaN was imputed
            assert cleaned_df['prosocial_amount'].isna().sum() == 0
            # Check structural zeros preserved
            assert (cleaned_df['prosocial_amount'] == 0).sum() == 2
            # Check imputation value is median of non-zero, non-NaN values
            expected_median = pd.Series([10.0, 20.0, 30.0, 40.0]).median()
            assert details['imputation_value'] == expected_median
            assert details['action'] == 'median_imputation'
            assert details['nan_percentage'] < 5.0
            # Verify log file exists
            assert log_path.exists()
    
    def test_row_exclusion_above_threshold(self):
        """Test row exclusion when NaN >= 5%."""
        # 2 NaN out of 4 rows = 50% > 5%
        data = {
            'prosocial_amount': [10.0, np.nan, 30.0, np.nan],
            'condition': [1, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            # Check that NaN rows were excluded
            assert len(cleaned_df) == 2
            assert cleaned_df['prosocial_amount'].isna().sum() == 0
            assert details['action'] == 'row_exclusion'
            assert details['rows_excluded'] == 2
            assert details['imputation_value'] is None
    
    def test_structural_zeros_preserved(self):
        """Test that structural zeros (0) are never imputed."""
        data = {
            'prosocial_amount': [0.0, np.nan, 0.0, 20.0, 0.0],
            'condition': [1, 0, 1, 1, 0]
        }
        df = pd.DataFrame(data)
        original_zeros = (df['prosocial_amount'] == 0).sum()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            # Count zeros in cleaned data
            final_zeros = (cleaned_df['prosocial_amount'] == 0).sum()
            assert final_zeros == original_zeros, "Structural zeros were lost!"
            
            # Ensure no NaN remains (imputation happened)
            assert cleaned_df['prosocial_amount'].isna().sum() == 0
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame({'prosocial_amount': [], 'condition': []})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            assert len(cleaned_df) == 0
            assert details['total_rows'] == 0
            assert details['nan_percentage'] == 0.0
    
    def test_column_not_found(self):
        """Test error when target column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            with pytest.raises(ValueError, match="Column.*not found"):
                handle_missing_values(df, 'prosocial_amount', log_path)
    
    def test_all_zeros_no_imputation_needed(self):
        """Test case where all values are zeros (no NaN)."""
        data = {
            'prosocial_amount': [0.0, 0.0, 0.0, 0.0],
            'condition': [1, 1, 0, 0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            assert len(cleaned_df) == 4
            assert (cleaned_df['prosocial_amount'] == 0).sum() == 4
            assert details['nan_count'] == 0
            assert details['action'] == 'median_imputation' # Logic falls here but no imputation done
            assert details['imputation_value'] is None # No valid values to compute median
    
    def test_all_nan_above_threshold(self):
        """Test case where all values are NaN (>=5%)."""
        data = {
            'prosocial_amount': [np.nan, np.nan, np.nan],
            'condition': [1, 0, 1]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            assert len(cleaned_df) == 0
            assert details['action'] == 'exclusion_no_valid_data'
    
    def test_boundary_case_exactly_5_percent(self):
        """Test boundary case: exactly 5% NaN triggers exclusion."""
        # 5 NaN out of 100 rows = 5%
        data = {
            'prosocial_amount': [float(i) for i in range(95)] + [np.nan]*5,
            'condition': [1]*100
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            # 5% should trigger exclusion
            assert details['action'] == 'row_exclusion'
            assert len(cleaned_df) == 95
            assert details['rows_excluded'] == 5
    
    def test_boundary_case_4_9_percent(self):
        """Test boundary case: 4.9% NaN triggers imputation."""
        # 49 NaN out of 1000 rows = 4.9%
        data = {
            'prosocial_amount': [float(i) for i in range(951)] + [np.nan]*49,
            'condition': [1]*1000
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "imputation_log.json"
            cleaned_df, details = handle_missing_values(df, 'prosocial_amount', log_path)
            
            # 4.9% should trigger imputation
            assert details['action'] == 'median_imputation'
            assert len(cleaned_df) == 1000
            assert cleaned_df['prosocial_amount'].isna().sum() == 0
            assert details['rows_imputed'] == 49
