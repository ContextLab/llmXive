import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.train import extract_primary_element, assign_element_families, load_family_map

def test_extract_primary_element_tie_breaker():
    """
    Test that the primary element extraction correctly handles ties
    by selecting the element with the higher atomic number.
    """
    # Simulate a row with a tie between Zr (40) and Hf (72)
    # Composition: "Zr-Hf-Cu" with fractions Zr=0.3, Hf=0.3, Cu=0.2
    # Expected primary: Hf (due to higher atomic number)
    
    row_data = pd.Series({
        'composition': 'Zr-Hf-Cu',
        'Zr': 0.3,
        'Hf': 0.3,
        'Cu': 0.2
    })
    
    primary, fractions = extract_primary_element('Zr-Hf-Cu', row_data)
    
    assert primary == 'Hf', f"Expected Hf (tie-breaker), got {primary}"
    assert fractions['Zr'] == 0.3
    assert fractions['Hf'] == 0.3

def test_extract_primary_element_max_fraction():
    """
    Test that the primary element is the one with the highest fraction.
    """
    row_data = pd.Series({
        'composition': 'Zr-Cu-Al',
        'Zr': 0.5,
        'Cu': 0.3,
        'Al': 0.2
    })
    
    primary, _ = extract_primary_element('Zr-Cu-Al', row_data)
    assert primary == 'Zr', f"Expected Zr (max fraction), got {primary}"

def test_assign_element_families_consistency():
    """
    Test that family assignment is consistent with the family_map.
    """
    family_map = {
        'Zr': 'Zr-family',
        'Hf': 'Zr-family',
        'Cu': 'Cu-family',
        'Ti': 'Zr-family',
        'Al': 'Al-family'
    }
    
    df = pd.DataFrame({
        'composition': ['Zr-Cu-Al', 'Hf-Ti-Cu'],
        'Zr': [0.5, 0.0],
        'Cu': [0.3, 0.2],
        'Al': [0.2, 0.0],
        'Hf': [0.0, 0.5],
        'Ti': [0.0, 0.3]
    })
    
    result_df = assign_element_families(df, family_map)
    
    # Row 0: Zr is primary -> Zr-family
    # Row 1: Hf is primary -> Zr-family
    assert result_df.iloc[0]['family'] == 'Zr-family'
    assert result_df.iloc[1]['family'] == 'Zr-family'
    
    # Verify primary elements
    assert result_df.iloc[0]['primary_element'] == 'Zr'
    assert result_df.iloc[1]['primary_element'] == 'Hf'

def test_load_family_map():
    """
    Test that the family map loads correctly from YAML.
    """
    # Create a temporary YAML file for testing
    import tempfile
    import yaml
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({'Zr': 'Zr-family', 'Cu': 'Cu-family'}, f)
        temp_path = f.name
    
    try:
        map_data = load_family_map(temp_path)
        assert map_data['Zr'] == 'Zr-family'
        assert map_data['Cu'] == 'Cu-family'
    finally:
        os.unlink(temp_path)