"""
Unit tests for data preprocessing logic.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code.data.preprocess import preprocess_data, normalize_units

def test_preprocess_single_phase_filter():
    """Test filtering for single-phase alloys."""
    data = {
        'composition': ['AlCoCrFeNi', 'FeMnNi', 'CoCrFeMnNi', 'TiZrHfNb'],
        'phase': ['Single', 'Multi', 'Single-phase', 'Dual'],
        'temp': [25, 25, 25, 25],
        'yield_strength': [200, 300, 400, 500]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = preprocess_data(temp_path)
        # Should keep 'Single' and 'Single-phase'
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert all(result['phase'].str.lower().isin(['single', 'single-phase']))
    finally:
        os.unlink(temp_path)

def test_preprocess_temperature_filter():
    """Test filtering for room temperature (20-25°C)."""
    data = {
        'composition': ['A', 'B', 'C', 'D'],
        'phase': ['Single', 'Single', 'Single', 'Single'],
        'temp': [20, 24, 26, 15],
        'yield_strength': [100, 200, 300, 400]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = preprocess_data(temp_path)
        # Should keep 20 and 24
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert all((result['temp'] >= 20) & (result['temp'] <= 25))
    finally:
        os.unlink(temp_path)

def test_preprocess_missing_yield_strength():
    """Test dropping rows with missing yield strength."""
    data = {
        'composition': ['A', 'B', 'C'],
        'phase': ['Single', 'Single', 'Single'],
        'temp': [25, 25, 25],
        'yield_strength': [100, np.nan, 300]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        result = preprocess_data(temp_path)
        # Should drop the NaN row
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert not result['yield_strength'].isna().any()
    finally:
        os.unlink(temp_path)

def test_normalize_units_with_unit_column():
    """Test normalization when unit column is present."""
    data = {
        'composition': ['A', 'B'],
        'yield_strength': [100, 1000],
        'unit': ['MPa', 'GPa']
    }
    df = pd.DataFrame(data)
    
    result = normalize_units(df)
    
    # 100 MPa -> 100 MPa
    # 1000 GPa -> 1000000 MPa
    assert result['yield_strength'].iloc[0] == 100.0
    assert result['yield_strength'].iloc[1] == 1000000.0

def test_normalize_units_no_unit_column():
    """Test normalization when unit column is missing (assumes MPa)."""
    data = {
        'composition': ['A', 'B'],
        'yield_strength': [100, 200]
    }
    df = pd.DataFrame(data)
    
    result = normalize_units(df)
    
    # Values should remain unchanged
    assert result['yield_strength'].iloc[0] == 100.0
    assert result['yield_strength'].iloc[1] == 200.0