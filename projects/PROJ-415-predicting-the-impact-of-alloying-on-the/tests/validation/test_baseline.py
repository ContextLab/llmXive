"""
Tests for T030: Baseline Shift Calculation.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validation.baseline import get_pure_host_baseline, calculate_baseline_shifts
from code.config import CURATED_DIR

@pytest.fixture
def sample_curated_data():
    """Create a mock curated dataframe for testing."""
    data = {
        'host_id': ['Cu', 'Cu', 'Cu', 'Al', 'Al'],
        'solute_id': ['Cu', 'Zn', 'Ni', 'Al', 'Mg'],
        'concentration': [0.0, 0.1, 0.2, 0.0, 0.1],
        'activation_energy': [1.5, 1.6, 1.7, 1.2, 1.3]
    }
    return pd.DataFrame(data)

def test_get_pure_host_baseline_exists(sample_curated_data):
    """Test retrieving baseline for a host that has pure entries."""
    baseline = get_pure_host_baseline('Cu', sample_curated_data)
    assert baseline is not None
    # There is one pure entry (1.5), so median is 1.5
    assert baseline == 1.5

def test_get_pure_host_baseline_missing(sample_curated_data):
    """Test retrieving baseline for a host that has NO pure entries."""
    # Add a host with no concentration=0
    no_pure_data = sample_curated_data.copy()
    no_pure_data = no_pure_data[no_pure_data['host_id'] != 'Cu'] # Remove Cu (has pure)
    no_pure_data.loc[len(no_pure_data)] = ['Ag', 'Ag', 0.1, 1.0] # Ag with only 0.1 conc
    
    baseline = get_pure_host_baseline('Ag', no_pure_data)
    assert baseline is None

def test_calculate_baseline_shifts(sample_curated_data):
    """Test the full calculation logic."""
    result = calculate_baseline_shifts(sample_curated_data)
    
    assert len(result) == 5 # All rows should have baselines
    
    # Check columns
    assert 'baseline_shift' in result.columns
    assert 'pure_host_baseline' in result.columns
    
    # Check specific values
    # Row 0: Cu, conc 0.0, E=1.5, base=1.5 -> shift=0.0
    row_0 = result[result['host_id'] == 'Cu'].iloc[0] # Might be mixed order, check by index if needed
    # Better check:
    cu_rows = result[result['host_id'] == 'Cu']
    assert all(cu_rows['pure_host_baseline'] == 1.5)
    assert (cu_rows['activation_energy'] - cu_rows['pure_host_baseline'] == cu_rows['baseline_shift']).all()

def test_calculate_baseline_shifts_excludes_missing():
    """Test that rows without pure host baseline are excluded."""
    data = {
        'host_id': ['Cu', 'Ag'],
        'solute_id': ['Cu', 'Ag'],
        'concentration': [0.0, 0.1],
        'activation_energy': [1.5, 1.6]
    }
    df = pd.DataFrame(data)
    
    # Cu has pure (0.0), Ag does not (only 0.1)
    result = calculate_baseline_shifts(df)
    
    assert len(result) == 1 # Only Cu row
    assert result['host_id'].iloc[0] == 'Cu'
