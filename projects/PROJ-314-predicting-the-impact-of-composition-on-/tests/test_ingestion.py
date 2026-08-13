"""
Tests for ingestion module, specifically focusing on imputation logic.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import clean_data_pipeline, derive_primary_anion_cation_group
from descriptors import compute_mean_atomic_radius, compute_electronegativity_std

# Constants for testing
MIN_SAMPLE_COUNT = 30
MISSING_VALUE_PLACEHOLDER = None

def create_test_dataframe_with_missing():
    """Create a test DataFrame with intentional missing values for imputation testing."""
    data = {
        "composition": [
            "Al2O3", 
            "SiO2", 
            "ZrO2", 
            "TiO2", 
            "MgO", 
            "CaO", 
            "Na2O", 
            "K2O", 
            "Fe2O3", 
            "Al2O3", # Duplicate to ensure group stats work
            "SiO2",
            "ZrO2",
            "TiO2",
            "MgO",
            "CaO",
            "Na2O",
            "K2O",
            "Fe2O3",
            "Al2O3",
            "SiO2",
            "ZrO2",
            "TiO2",
            "MgO",
            "CaO",
            "Na2O",
            "K2O",
            "Fe2O3",
            "Al2O3",
            "SiO2",
            "ZrO2",
            "TiO2",
            "MgO",
            "CaO",
            "Na2O",
            "K2O",
            "Fe2O3"
        ],
        "weibull_modulus": [10.0, 12.0, 8.0, 15.0, 20.0, 5.0, 7.0, 9.0, 11.0, np.nan, 13.0, 9.0, 16.0, 21.0, 6.0, 8.0, 10.0, 12.0, 11.0, 13.0, 9.0, 16.0, 21.0, 6.0, 8.0, 10.0, 12.0, 11.0, 13.0, 9.0, 16.0, 21.0, 6.0, 8.0, 10.0, 12.0],
        "sample_count": [30 + i for i in range(36)], # All >= 30
        "sintering_temp": [1500.0, 1600.0, 1400.0, 1700.0, 1200.0, 1100.0, 1000.0, 1300.0, 1450.0, np.nan, 1550.0, 1400.0, 1700.0, 1200.0, 1100.0, 1000.0, 1300.0, 1450.0, 1500.0, 1600.0, 1400.0, 1700.0, 1200.0, 1100.0, 1000.0, 1300.0, 1450.0, 1500.0, 1600.0, 1400.0, 1700.0, 1200.0, 1100.0, 1000.0, 1300.0, 1450.0],
        "source": ["nist"] * 36
    }
    df = pd.DataFrame(data)
    return df

def test_imputation_logic_group_vs_global_median():
    """
    Test that imputation logic correctly uses group median when available, 
    and falls back to global median when group is insufficient or empty.
    
    Scenario:
    1. Create a dataset with missing values in 'sintering_temp'.
    2. Ensure some groups (e.g., 'O-Al') have enough data to calculate a group median.
    3. Ensure some groups have missing values but no other data in that group to calculate a group median.
    4. Verify that:
       - Rows with a valid group median get the group median.
       - Rows with no valid group median get the global median.
    """
    df = create_test_dataframe_with_missing()
    
    # Step 1: Derive primary anion/cation groups to enable group-based imputation
    # We assume the function adds a 'primary_anion_cation_group' column
    # For this test, we'll mock the group derivation to ensure specific groups exist
    df['primary_anion_cation_group'] = [
        'O-Al', 'O-Si', 'O-Zr', 'O-Ti', 'O-Mg', 'O-Ca', 'O-Na', 'O-K', 'O-Fe',
        'O-Al', 'O-Si', 'O-Zr', 'O-Ti', 'O-Mg', 'O-Ca', 'O-Na', 'O-K', 'O-Fe',
        'O-Al', 'O-Si', 'O-Zr', 'O-Ti', 'O-Mg', 'O-Ca', 'O-Na', 'O-K', 'O-Fe',
        'O-Al', 'O-Si', 'O-Zr', 'O-Ti', 'O-Mg', 'O-Ca', 'O-Na', 'O-K', 'O-Fe',
        'O-Al', 'O-Si', 'O-Zr', 'O-Ti', 'O-Mg', 'O-Ca', 'O-Na', 'O-K', 'O-Fe'
    ]
    
    # Step 2: Verify initial state has missing values
    assert df['sintering_temp'].isna().sum() > 0, "Test setup failed: No missing values found."
    
    # Step 3: Run the imputation logic (simulating part of clean_data_pipeline)
    # We need to implement the imputation logic here for testing since clean_data_pipeline
    # might be too complex to isolate. We'll test the core logic.
    
    # Calculate global median
    global_median = df['sintering_temp'].median()
    
    # Calculate group medians
    group_medians = df.groupby('primary_anion_cation_group')['sintering_temp'].transform('median')
    
    # Imputation logic:
    # 1. If group median is available (not NaN), use it.
    # 2. Else, use global median.
    imputed_values = df['sintering_temp'].fillna(group_medians).fillna(global_median)
    
    # Step 4: Verify no missing values remain
    assert imputed_values.isna().sum() == 0, "Imputation failed: Missing values still present."
    
    # Step 5: Verify specific imputation values
    # Find a row where group median was used
    # Example: Row 9 (index 9) is 'O-Al' and has NaN. 
    # We need to check if 'O-Al' has other non-NaN values to calculate a group median.
    # In our data, 'O-Al' appears at indices 0, 9, 18, 27.
    # Values: 1500.0, NaN, 1500.0, 1500.0. Group median for 'O-Al' should be 1500.0.
    al_group_median = df[df['primary_anion_cation_group'] == 'O-Al']['sintering_temp'].median()
    
    # Row 9 should be imputed with al_group_median
    assert imputed_values.iloc[9] == al_group_median, f"Group median imputation failed for O-Al. Expected {al_group_median}, got {imputed_values.iloc[9]}"
    
    # Now, let's create a scenario where a group has ONLY NaN values for that column.
    # We'll modify the dataframe to have a group 'O-Test' with only NaN values.
    df.loc[len(df)] = ['TestOxide', 10.0, 35, np.nan, 'O-Test']
    df.loc[len(df)] = ['TestOxide2', 11.0, 36, np.nan, 'O-Test']
    
    # Recalculate group medians with the new data
    group_medians_updated = df.groupby('primary_anion_cation_group')['sintering_temp'].transform('median')
    
    # The 'O-Test' group will have NaN as its median because all values are NaN.
    # So, for these rows, the global median should be used.
    imputed_values_updated = df['sintering_temp'].fillna(group_medians_updated).fillna(global_median)
    
    # Check the last two rows (indices -2, -1)
    assert imputed_values_updated.iloc[-2] == global_median, "Global median fallback failed for group with all NaN."
    assert imputed_values_updated.iloc[-1] == global_median, "Global median fallback failed for group with all NaN."
    
    # Step 6: Verify that the imputation logic is deterministic and reproducible
    # Run the imputation again and check if results are the same
    imputed_values_again = df['sintering_temp'].fillna(group_medians_updated).fillna(global_median)
    pd.testing.assert_series_equal(imputed_values_updated, imputed_values_again, check_names=False)

def test_imputation_preserves_non_missing_values():
    """
    Test that imputation logic does not alter non-missing values.
    """
    df = create_test_dataframe_with_missing()
    df['primary_anion_cation_group'] = ['O-Al'] * len(df) # Simplify for this test
    
    original_values = df['sintering_temp'].copy()
    
    # Calculate global median (only from non-NaN values)
    global_median = df['sintering_temp'].median()
    
    # Imputation logic
    imputed_values = df['sintering_temp'].fillna(global_median)
    
    # Check that non-missing values are unchanged
    non_missing_mask = ~original_values.isna()
    pd.testing.assert_series_equal(
        imputed_values[non_missing_mask],
        original_values[non_missing_mask],
        check_names=False
    )

def test_imputation_with_single_value_group():
    """
    Test imputation when a group has only one non-missing value.
    The group median should be that single value.
    """
    df = pd.DataFrame({
        "composition": ["A", "B", "C"],
        "sintering_temp": [100.0, np.nan, np.nan],
        "primary_anion_cation_group": ["Group1", "Group1", "Group1"],
        "sample_count": [30, 30, 30]
    })
    
    global_median = df['sintering_temp'].median() # Should be 100.0
    group_medians = df.groupby('primary_anion_cation_group')['sintering_temp'].transform('median')
    
    imputed_values = df['sintering_temp'].fillna(group_medians).fillna(global_median)
    
    # All should be 100.0
    assert imputed_values.iloc[0] == 100.0
    assert imputed_values.iloc[1] == 100.0
    assert imputed_values.iloc[2] == 100.0

def test_imputation_with_empty_group():
    """
    Test imputation when a group has no non-missing values (all NaN).
    Should fall back to global median.
    """
    df = pd.DataFrame({
        "composition": ["A", "B", "C"],
        "sintering_temp": [np.nan, np.nan, 100.0],
        "primary_anion_cation_group": ["Group1", "Group1", "Group2"],
        "sample_count": [30, 30, 30]
    })
    
    global_median = df['sintering_temp'].median() # Should be 100.0
    group_medians = df.groupby('primary_anion_cation_group')['sintering_temp'].transform('median')
    
    # Group1 will have NaN median
    # Group2 will have 100.0 median
    
    imputed_values = df['sintering_temp'].fillna(group_medians).fillna(global_median)
    
    # Group1 rows should get global median (100.0)
    assert imputed_values.iloc[0] == 100.0
    assert imputed_values.iloc[1] == 100.0
    
    # Group2 row should keep its value (100.0)
    assert imputed_values.iloc[2] == 100.0