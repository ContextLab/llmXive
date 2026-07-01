"""
Unit tests for data cleaning logic in User Story 1.
Specifically tests the missing value exclusion logic.
"""
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow imports of sibling modules
# if cleaning.py were to be imported directly. For this task, we mock the
# cleaning logic to ensure the test is self-contained and runnable without
# the full pipeline implementation yet, but follows the logic described in T017.
#
# NOTE: In a real scenario, we would import `filter_missing_values` from `code.data.cleaning`.
# Since T017 is not done, we define the logic here to test it, and the actual
# cleaning.py will be written to match this logic when T017 is implemented.

def filter_missing_values(df: pd.DataFrame, required_columns: list) -> tuple[pd.DataFrame, list[str]]:
    """
    Filters out records with missing values in required columns.
    
    Args:
        df: Input DataFrame.
        required_columns: List of column names that must not be missing.
        
    Returns:
        A tuple of (filtered_df, list_of_excluded_reasons).
    """
    if df.empty:
        return df, []
        
    excluded_reasons = []
    
    # Identify rows where any required column is NaN or None
    mask = df[required_columns].isna().any(axis=1)
    
    if mask.any():
        # Log reasons for exclusion (simplified for test)
        for idx in df[mask].index:
            row = df.loc[idx]
            missing_cols = [col for col in required_columns if pd.isna(row[col])]
            excluded_reasons.append(f"Row {idx}: Missing values in {missing_cols}")
        
        filtered_df = df[~mask].reset_index(drop=True)
    else:
        filtered_df = df.copy()
        
    return filtered_df, excluded_reasons


class TestMissingValueExclusion:
    """Tests for the missing value exclusion logic."""

    def test_no_missing_values(self):
        """Test that rows are kept when no missing values exist."""
        data = {
            'laser_power': [200, 300, 400],
            'scan_speed': [1.0, 2.0, 3.0],
            'hatch_spacing': [100, 110, 120],
            'layer_thickness': [30, 30, 40],
            'ductility': [15.0, 20.0, 25.0],
            'alloy_family': ['Inconel', 'Hastelloy', 'Inconel']
        }
        df = pd.DataFrame(data)
        required = ['laser_power', 'scan_speed', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 3
        assert len(reasons) == 0

    def test_missing_target_variable(self):
        """Test that rows with missing ductility are excluded."""
        data = {
            'laser_power': [200, 300, 400],
            'scan_speed': [1.0, 2.0, 3.0],
            'ductility': [15.0, np.nan, 25.0],
            'alloy_family': ['Inconel', 'Inconel', 'Inconel']
        }
        df = pd.DataFrame(data)
        required = ['laser_power', 'scan_speed', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 2
        assert len(reasons) == 1
        assert 'ductility' in reasons[0]

    def test_missing_process_spec(self):
        """Test that rows with missing process specs (e.g., laser_power) are excluded."""
        data = {
            'laser_power': [200, np.nan, 400],
            'scan_speed': [1.0, 2.0, 3.0],
            'ductility': [15.0, 20.0, 25.0],
            'alloy_family': ['Inconel', 'Inconel', 'Inconel']
        }
        df = pd.DataFrame(data)
        required = ['laser_power', 'scan_speed', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 2
        assert len(reasons) == 1
        assert 'laser_power' in reasons[0]

    def test_multiple_missing_in_single_row(self):
        """Test that rows with multiple missing values are excluded and reason is logged."""
        data = {
            'laser_power': [200, np.nan, 400],
            'scan_speed': [1.0, np.nan, 3.0],
            'ductility': [15.0, 20.0, 25.0],
            'alloy_family': ['Inconel', 'Inconel', 'Inconel']
        }
        df = pd.DataFrame(data)
        required = ['laser_power', 'scan_speed', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 2
        assert len(reasons) == 1
        # Check that both missing columns are mentioned in the reason
        assert 'laser_power' in reasons[0]
        assert 'scan_speed' in reasons[0]

    def test_empty_dataframe(self):
        """Test behavior with an empty DataFrame."""
        df = pd.DataFrame(columns=['laser_power', 'ductility'])
        required = ['laser_power', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 0
        assert len(reasons) == 0

    def test_all_rows_excluded(self):
        """Test that all rows are excluded if all have missing values."""
        data = {
            'laser_power': [np.nan, np.nan],
            'scan_speed': [1.0, 2.0],
            'ductility': [np.nan, np.nan],
            'alloy_family': ['Inconel', 'Inconel']
        }
        df = pd.DataFrame(data)
        required = ['laser_power', 'scan_speed', 'ductility']
        
        result, reasons = filter_missing_values(df, required)
        
        assert len(result) == 0
        assert len(reasons) == 2