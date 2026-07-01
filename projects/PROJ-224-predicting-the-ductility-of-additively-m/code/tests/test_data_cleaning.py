import pytest
import pandas as pd
import numpy as np
from code.data.cleaning import convert_units, filter_missing_values, map_alloy_flags

def test_placeholder_cleaning():
    """Placeholder test to ensure the test suite runs."""
    assert True

def test_unit_conversion_logic():
    """Unit test for unit conversion logic in code/data/cleaning.py.
    
    Verifies that:
    1. Watts are converted correctly (1 W = 1 W)
    2. mm/s are converted correctly (1 mm/s = 1 mm/s)
    3. µm are converted to mm (1000 µm = 1 mm)
    4. % are converted correctly (1% = 1%)
    """
    # Create test data with mixed units
    data = {
        'laser_power': [100, 200],  # Already in W
        'scan_speed': [500, 1000],  # Already in mm/s
        'layer_thickness': [100, 200],  # In µm
        'ductility': [10.5, 15.2]  # Already in %
    }
    df = pd.DataFrame(data)
    
    # Apply conversion
    result = convert_units(df)
    
    # Verify layer_thickness was converted from µm to mm
    assert result['layer_thickness'].iloc[0] == 0.1  # 100 µm -> 0.1 mm
    assert result['layer_thickness'].iloc[1] == 0.2  # 200 µm -> 0.2 mm
    
    # Verify other columns remain unchanged
    assert result['laser_power'].iloc[0] == 100
    assert result['scan_speed'].iloc[0] == 500
    assert result['ductility'].iloc[0] == 10.5

def test_missing_value_exclusion():
    """Unit test for missing value exclusion logic in code/data/cleaning.py.
    
    Verifies that:
    1. Rows with missing ductility are excluded
    2. Rows with missing process parameters (laser_power, scan_speed, hatch_spacing, layer_thickness) are excluded
    3. Rows with complete data are retained
    4. The function logs the reason for exclusion
    """
    # Create test data with various missing value scenarios
    data = {
        'laser_power': [100.0, 200.0, np.nan, 400.0, 500.0],
        'scan_speed': [500.0, np.nan, 700.0, 800.0, 900.0],
        'hatch_spacing': [100.0, 200.0, 300.0, np.nan, 500.0],
        'layer_thickness': [50.0, 60.0, 70.0, 80.0, np.nan],
        'ductility': [10.0, 15.0, 20.0, 25.0, 30.0],
        'alloy_family': ['Inconel', 'Inconel', 'Hastelloy', 'Inconel', 'Hastelloy']
    }
    df = pd.DataFrame(data)
    
    # Apply filtering
    result, excluded_reasons = filter_missing_values(df)
    
    # Verify that only the first row (complete data) is retained
    # Row 0: Complete -> Retained
    # Row 1: Missing scan_speed -> Excluded
    # Row 2: Missing laser_power -> Excluded
    # Row 3: Missing hatch_spacing -> Excluded
    # Row 4: Missing layer_thickness -> Excluded
    assert len(result) == 1
    assert result.iloc[0]['laser_power'] == 100.0
    assert result.iloc[0]['scan_speed'] == 500.0
    assert result.iloc[0]['hatch_spacing'] == 100.0
    assert result.iloc[0]['layer_thickness'] == 50.0
    assert result.iloc[0]['ductility'] == 10.0
    
    # Verify that all excluded rows are in the reasons list
    assert len(excluded_reasons) == 4
    
    # Verify that the function correctly identifies missing values
    # and logs the appropriate reasons
    reasons_text = ' '.join(str(r) for r in excluded_reasons)
    assert 'scan_speed' in reasons_text or 'laser_power' in reasons_text or 'hatch_spacing' in reasons_text or 'layer_thickness' in reasons_text

def test_alloy_flag_mapping():
    """Unit test for alloy flag mapping logic in code/data/cleaning.py.
    
    Verifies that:
    1. Alloy composition is correctly mapped to binary flags
    2. Elements not present in the composition are flagged as 0
    3. Elements present in the composition are flagged as 1
    """
    # Create test data with alloy compositions
    data = {
        'alloy_composition': [
            'Cr:15, Al:5, Ti:3, Co:10, Mo:2, W:1',
            'Cr:20, Al:8, Ti:5, Co:15, Mo:4, W:2',
            'Cr:10, Al:2, Ti:1, Co:5, Mo:1, W:0.5',
            'Al:10, Ti:5',  # Missing some elements
            'Cr:25, Mo:10, W:5'  # Missing some elements
        ]
    }
    df = pd.DataFrame(data)
    
    # Apply mapping
    result = map_alloy_flags(df)
    
    # Verify that all expected columns are present
    expected_columns = ['Cr_flag', 'Al_flag', 'Ti_flag', 'Co_flag', 'Mo_flag', 'W_flag']
    for col in expected_columns:
        assert col in result.columns
    
    # Verify that the flags are correctly set
    # Row 0: All elements present
    assert result['Cr_flag'].iloc[0] == 1
    assert result['Al_flag'].iloc[0] == 1
    assert result['Ti_flag'].iloc[0] == 1
    assert result['Co_flag'].iloc[0] == 1
    assert result['Mo_flag'].iloc[0] == 1
    assert result['W_flag'].iloc[0] == 1
    
    # Row 3: Only Al and Ti present
    assert result['Cr_flag'].iloc[3] == 0
    assert result['Al_flag'].iloc[3] == 1
    assert result['Ti_flag'].iloc[3] == 1
    assert result['Co_flag'].iloc[3] == 0
    assert result['Mo_flag'].iloc[3] == 0
    assert result['W_flag'].iloc[3] == 0
    
    # Row 4: Cr, Mo, W present
    assert result['Cr_flag'].iloc[4] == 1
    assert result['Al_flag'].iloc[4] == 0
    assert result['Ti_flag'].iloc[4] == 0
    assert result['Co_flag'].iloc[4] == 0
    assert result['Mo_flag'].iloc[4] == 1
    assert result['W_flag'].iloc[4] == 1