"""
Unit tests for data filtering logic, specifically focusing on null-value exclusion.

This module contains tests for the null-handling behavior defined in User Story 1 (US1).
It verifies that the filtering pipeline correctly excludes rows with missing values
in critical fields (Shannon index, Cognitive scores, and required covariates).
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import shutil

# Add src to path to allow imports during local testing
# In the CI environment, this is handled by the working directory setup
src_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

from data.filtering import filter_null_values, validate_required_columns

# Constants for test data
REQUIRED_COVARIATES = ['age', 'sex', 'bmi', 'fiber', 'antibiotics']
CRITICAL_METRICS = ['shannon', 'cognitive_score']
ALL_CRITICAL_FIELDS = REQUIRED_COVARIATES + CRITICAL_METRICS


def create_test_dataframe():
    """
    Creates a synthetic test dataframe with various null patterns.
    
    Returns:
        pd.DataFrame: A dataframe with 10 rows, containing:
            - Row 0: Complete data (should pass)
            - Row 1: Missing shannon (should fail)
            - Row 2: Missing cognitive_score (should fail)
            - Row 3: Missing age (should fail)
            - Row 4: Missing bmi (should fail)
            - Row 5: Missing fiber (should fail)
            - Row 6: Missing antibiotics (should fail)
            - Row 7: Multiple missing fields (should fail)
            - Row 8: Complete data (should pass)
            - Row 9: NaN in a non-critical field (should pass)
    """
    data = {
        'participant_id': [f'P{i:03d}' for i in range(10)],
        'age': [65, 70, 72, np.nan, 68, 75, 66, 71, 69, 70],
        'sex': ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F'],
        'bmi': [24.5, 26.1, 22.3, 25.0, np.nan, 23.8, 27.2, 24.9, 25.5, 26.0],
        'fiber': [18.2, 22.5, 15.8, 20.1, 19.5, np.nan, 21.3, 17.9, 23.1, 20.0],
        'antibiotics': [0, 1, 0, 0, 1, 0, np.nan, 1, 0, 1],
        'shannon': [3.5, 3.2, 3.8, 3.1, 3.6, 3.4, 3.7, np.nan, 3.3, 3.9],
        'cognitive_score': [85, 82, 88, 84, 86, 83, 87, 85, np.nan, 89],
        'non_critical': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', np.nan]
    }
    
    return pd.DataFrame(data)


class TestNullValueExclusion:
    """
    Test suite for null-value exclusion logic in the filtering pipeline.
    
    These tests ensure that the filtering function correctly identifies and removes
    rows with missing values in critical fields while preserving rows with missing
    values in non-critical fields.
    """
    
    def test_filter_removes_rows_with_missing_critical_metrics(self):
        """
        Test that rows with missing Shannon or Cognitive scores are excluded.
        
        Expected behavior:
        - Row 1 (missing shannon) should be removed
        - Row 2 (missing cognitive_score) should be removed
        - Row 7 (missing both) should be removed
        """
        df = create_test_dataframe()
        result = filter_null_values(df, critical_fields=CRITICAL_METRICS)
        
        # Should have 6 rows remaining (0, 3, 4, 5, 6, 8, 9) - wait, let's recount
        # Original: 10 rows
        # Removed: 1, 2, 7 (3 rows)
        # Also removed: 3 (age), 4 (bmi), 5 (fiber), 6 (antibiotics)
        # Total removed: 7 rows
        # Remaining: 3 rows (0, 8, 9)
        
        expected_indices = [0, 8, 9]
        assert len(result) == len(expected_indices), \
            f"Expected {len(expected_indices)} rows, got {len(result)}"
        
        # Verify the specific rows that should remain
        assert list(result['participant_id']) == ['P000', 'P008', 'P009']
        
        # Verify no NaN values in critical fields
        for field in CRITICAL_METRICS:
            assert not result[field].isna().any(), \
                f"Found NaN values in critical field: {field}"
    
    def test_filter_removes_rows_with_missing_covariates(self):
        """
        Test that rows with missing required covariates (age, sex, bmi, fiber, antibiotics) are excluded.
        
        Expected behavior:
        - Row 3 (missing age) should be removed
        - Row 4 (missing bmi) should be removed
        - Row 5 (missing fiber) should be removed
        - Row 6 (missing antibiotics) should be removed
        """
        df = create_test_dataframe()
        result = filter_null_values(df, critical_fields=ALL_CRITICAL_FIELDS)
        
        # Rows with missing covariates: 3, 4, 5, 6
        # Rows with missing metrics: 1, 2, 7
        # Total removed: 7 rows
        # Remaining: 3 rows (0, 8, 9)
        
        assert len(result) == 3
        assert list(result['participant_id']) == ['P000', 'P008', 'P009']
        
        # Verify no NaN in covariates
        for cov in REQUIRED_COVARIATES:
            assert not result[cov].isna().any(), \
                f"Found NaN values in covariate: {cov}"
    
    def test_preserves_rows_with_missing_non_critical_fields(self):
        """
        Test that rows with missing values in non-critical fields are preserved.
        
        Expected behavior:
        - Row 9 has NaN in 'non_critical' field but should be preserved
        """
        df = create_test_dataframe()
        result = filter_null_values(df, critical_fields=CRITICAL_METRICS)
        
        # Row 9 should be present
        assert 'P009' in result['participant_id'].values
        
        # Verify the non_critical field can still be NaN
        row_9 = result[result['participant_id'] == 'P009']
        assert pd.isna(row_9['non_critical'].iloc[0]), \
            "Non-critical field should be allowed to be NaN"
    
    def test_empty_dataframe_handling(self):
        """
        Test that an empty dataframe is handled correctly.
        """
        df = pd.DataFrame(columns=ALL_CRITICAL_FIELDS)
        result = filter_null_values(df, critical_fields=CRITICAL_METRICS)
        
        assert len(result) == 0
        assert list(result.columns) == list(df.columns)
    
    def test_dataframe_with_all_nulls(self):
        """
        Test that a dataframe with all nulls in critical fields returns empty.
        """
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'shannon': [np.nan, np.nan],
            'cognitive_score': [np.nan, np.nan]
        })
        
        result = filter_null_values(df, critical_fields=CRITICAL_METRICS)
        
        assert len(result) == 0
    
    def test_dataframe_with_no_nulls(self):
        """
        Test that a dataframe with no nulls is returned unchanged.
        """
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'shannon': [3.5, 3.6],
            'cognitive_score': [85, 86]
        })
        
        result = filter_null_values(df, critical_fields=CRITICAL_METRICS)
        
        assert len(result) == len(df)
        assert list(result['participant_id']) == ['P001', 'P002']
    
    def test_validate_required_columns_raises_on_missing(self):
        """
        Test that validate_required_columns raises ValueError when required columns are missing.
        """
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'shannon': [3.5]
            # Missing 'cognitive_score'
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_required_columns(df, ALL_CRITICAL_FIELDS)
        
        assert 'cognitive_score' in str(exc_info.value)
    
    def test_validate_required_columns_passes_when_complete(self):
        """
        Test that validate_required_columns passes when all required columns exist.
        """
        df = pd.DataFrame({
            'participant_id': ['P001'],
            'age': [65],
            'sex': ['M'],
            'bmi': [24.5],
            'fiber': [18.2],
            'antibiotics': [0],
            'shannon': [3.5],
            'cognitive_score': [85]
        })
        
        # Should not raise
        validate_required_columns(df, ALL_CRITICAL_FIELDS)
    
    def test_filter_with_custom_critical_fields(self):
        """
        Test filtering with a custom set of critical fields.
        """
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'shannon': [3.5, np.nan, 3.7],
            'cognitive_score': [85, 86, np.nan],
            'custom_field': [1.0, 2.0, 3.0]
        })
        
        # Only filter on shannon
        result = filter_null_values(df, critical_fields=['shannon'])
        
        assert len(result) == 2
        assert 'P001' in result['participant_id'].values
        assert 'P003' in result['participant_id'].values
        assert 'P002' not in result['participant_id'].values
    
    def test_filter_preserves_data_integrity(self):
        """
        Test that filtering preserves the data integrity of remaining rows.
        """
        df = create_test_dataframe()
        original_row_0 = df.iloc[0].copy()
        
        result = filter_null_values(df, critical_fields=ALL_CRITICAL_FIELDS)
        
        # Find row 0 in result
        result_row_0 = result[result['participant_id'] == 'P000'].iloc[0]
        
        # Compare values (ignoring index)
        for col in df.columns:
            if col != 'participant_id':
                assert result_row_0[col] == original_row_0[col], \
                    f"Data integrity violated for column {col}"