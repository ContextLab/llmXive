import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from descriptors import (
    parse_composition,
    calculate_weighted_mean_radius,
    calculate_radius_mismatch,
    calculate_electronegativity_difference,
    calculate_vec,
    compute_descriptors,
    save_descriptors
)

def test_parse_composition_valid():
    """Test parsing a valid composition string."""
    comp_str = "Fe50Ni30Co20"
    result = parse_composition(comp_str)
    assert abs(result['Fe'] - 0.5) < 1e-6
    assert abs(result['Ni'] - 0.3) < 1e-6
    assert abs(result['Co'] - 0.2) < 1e-6

def test_parse_composition_normalization():
    """Test that composition is normalized if sum > 100."""
    comp_str = "Fe60Ni40" # Sum is 100, should be 0.6, 0.4
    result = parse_composition(comp_str)
    assert abs(result['Fe'] - 0.6) < 1e-6
    assert abs(result['Ni'] - 0.4) < 1e-6

def test_calculate_weighted_mean_radius():
    """Test weighted mean radius calculation."""
    # Fe radius ~126 pm, Ni ~124 pm, Co ~125 pm (approximate values from mendeleev)
    # Composition: Fe0.5, Ni0.3, Co0.2
    # Expected: 0.5*126 + 0.3*124 + 0.2*125 = 63 + 37.2 + 25 = 125.2
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    wmr = calculate_weighted_mean_radius(comp)
    assert wmr is not None
    assert 120 < wmr < 130 # Reasonable range check

def test_calculate_radius_mismatch():
    """Test radius mismatch calculation."""
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    mismatch = calculate_radius_mismatch(comp)
    assert mismatch is not None
    assert mismatch >= 0

def test_calculate_electronegativity_difference():
    """Test electronegativity difference calculation."""
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    diff = calculate_electronegativity_difference(comp)
    assert diff is not None
    assert diff >= 0

def test_calculate_vec():
    """Test VEC calculation."""
    comp = {'Fe': 0.5, 'Ni': 0.3, 'Co': 0.2}
    vec = calculate_vec(comp)
    assert vec is not None
    # Fe (Group 8), Ni (Group 10), Co (Group 9) -> 0.5*8 + 0.3*10 + 0.2*9 = 4 + 3 + 1.8 = 8.8
    # Note: Mendeleev group numbers might vary slightly, but should be in this range.
    assert 8 < vec < 10

def test_compute_descriptors():
    """Test full descriptor computation pipeline."""
    comp_str = "Fe50Ni30Co20"
    desc = compute_descriptors(comp_str)
    assert 'radius_mismatch' in desc
    assert 'electronegativity_diff' in desc
    assert 'VEC' in desc
    assert desc['radius_mismatch'] is not None
    assert desc['electronegativity_diff'] is not None
    assert desc['VEC'] is not None

def test_save_descriptors(tmp_path):
    """Test saving descriptors to CSV."""
    df = pd.DataFrame({
        'radius_mismatch': [0.1, 0.2, 0.3],
        'electronegativity_diff': [0.5, 0.6, 0.7],
        'VEC': [8.5, 8.6, 8.7]
    })
    output_file = tmp_path / "test_descriptors.csv"
    save_descriptors(df, output_file)
    
    assert output_file.exists()
    saved_df = pd.read_csv(output_file)
    assert list(saved_df.columns) == ['radius_mismatch', 'electronegativity_diff', 'VEC']
    assert len(saved_df) == 3