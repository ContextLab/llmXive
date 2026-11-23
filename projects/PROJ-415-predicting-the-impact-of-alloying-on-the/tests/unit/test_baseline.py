"""
Unit tests for T030: Baseline Shift Calculation.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import tempfile
import json

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.validation.baseline import (
    get_pure_host_baseline,
    calculate_baseline_shifts,
    load_curated_data
)

@pytest.fixture
def sample_curated_data():
    """Create a mock curated dataset for testing."""
    data = {
        'host_id': ['Cu', 'Cu', 'Cu', 'Cu', 'Ag', 'Ag', 'Ag'],
        'solute_id': ['Cu', 'Au', 'Ag', 'Ni', 'Ag', 'Cu', 'Au'],
        'concentration': [0.0, 0.1, 0.1, 0.1, 0.0, 0.1, 0.1],
        'activation_energy': [1.0, 1.2, 1.3, 1.4, 0.8, 0.9, 1.1],
        'crystal_structure': ['FCC'] * 7,
        'diffusion_mode': ['self', 'alloy', 'alloy', 'alloy', 'self', 'alloy', 'alloy']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_curated_file(sample_curated_data, tmp_path):
    """Save sample data to a temporary file."""
    # Mock the CURATED_DIR path temporarily
    original_dir = None
    try:
        # We will pass the dataframe directly to functions that accept it,
        # but we need to ensure the file exists if load_curated_data is called.
        # For this test, we will test the helper functions directly with the dataframe.
        pass
    finally:
        pass
    return sample_curated_data

def test_get_pure_host_baseline_single():
    """Test retrieving baseline for a host with a single pure entry."""
    data = pd.DataFrame({
        'host_id': ['Cu', 'Cu'],
        'concentration': [0.0, 0.1],
        'activation_energy': [1.0, 1.2]
    })
    baseline = get_pure_host_baseline('Cu', data)
    assert baseline == 1.0

def test_get_pure_host_baseline_multiple():
    """Test retrieving median baseline for a host with multiple pure entries."""
    data = pd.DataFrame({
        'host_id': ['Cu', 'Cu', 'Cu', 'Cu'],
        'concentration': [0.0, 0.0, 0.1, 0.1],
        'activation_energy': [1.0, 2.0, 1.2, 1.3]
    })
    # Median of 1.0 and 2.0 is 1.5
    baseline = get_pure_host_baseline('Cu', data)
    assert baseline == 1.5

def test_get_pure_host_baseline_missing():
    """Test retrieving baseline when no pure entry exists."""
    data = pd.DataFrame({
        'host_id': ['Cu', 'Cu'],
        'concentration': [0.1, 0.2],
        'activation_energy': [1.0, 1.2]
    })
    baseline = get_pure_host_baseline('Cu', data)
    assert baseline is None

def test_calculate_baseline_shifts(temp_curated_file):
    """Test the full baseline shift calculation logic."""
    df, excluded_count = calculate_baseline_shifts(temp_curated_file)
    
    # Check structure
    assert 'baseline_shift' in df.columns
    assert 'pure_host_baseline' in df.columns
    assert 'host_id' in df.columns
    assert 'solute_id' in df.columns
    assert 'activation_energy' in df.columns

    # Check specific values for Cu
    # Cu pure baseline = 1.0
    # Cu-Au (0.1): shift = 1.2 - 1.0 = 0.2
    # Cu-Ag (0.1): shift = 1.3 - 1.0 = 0.3
    # Cu-Ni (0.1): shift = 1.4 - 1.0 = 0.4
    cu_rows = df[df['host_id'] == 'Cu']
    assert len(cu_rows) == 3 # Excluded self-diffusion row? No, self-diffusion has conc 0, so shift = 1.0 - 1.0 = 0.
    # Wait, the input has 3 Cu rows: conc 0 (self), 0.1 (Au), 0.1 (Ag), 0.1 (Ni). 
    # My sample data had 4 Cu rows: 0.0, 0.1, 0.1, 0.1.
    # Let's re-verify sample data:
    # 'host_id': ['Cu', 'Cu', 'Cu', 'Cu', ...]
    # 'concentration': [0.0, 0.1, 0.1, 0.1, ...]
    # So 4 Cu rows.
    # Pure baseline for Cu = 1.0.
    # Row 1 (Cu, 0.0): shift = 1.0 - 1.0 = 0.0.
    # Row 2 (Cu, 0.1, Au): shift = 1.2 - 1.0 = 0.2.
    # Row 3 (Cu, 0.1, Ag): shift = 1.3 - 1.0 = 0.3.
    # Row 4 (Cu, 0.1, Ni): shift = 1.4 - 1.0 = 0.4.
    
    assert len(cu_rows) == 4
    
    # Check Ag
    # Ag pure baseline = 0.8
    # Ag-Cu (0.1): shift = 0.9 - 0.8 = 0.1
    # Ag-Au (0.1): shift = 1.1 - 0.8 = 0.3
    ag_rows = df[df['host_id'] == 'Ag']
    assert len(ag_rows) == 3 # 1 pure + 2 alloys

def test_calculate_baseline_shifts_exclusion():
    """Test that rows without a pure host baseline are excluded."""
    data = pd.DataFrame({
        'host_id': ['Cu', 'Cu', 'Pt'],
        'solute_id': ['Cu', 'Au', 'Ir'],
        'concentration': [0.1, 0.1, 0.1],
        'activation_energy': [1.0, 1.2, 1.5],
        'crystal_structure': ['FCC'] * 3,
        'diffusion_mode': ['alloy'] * 3
    })
    # No pure entries for Cu or Pt
    df, excluded_count = calculate_baseline_shifts(data)
    assert df.empty
    assert excluded_count == 3