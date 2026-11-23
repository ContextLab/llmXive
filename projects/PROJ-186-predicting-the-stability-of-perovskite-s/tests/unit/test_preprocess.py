"""
Unit tests for code/data/preprocess.py (Task T016).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data.preprocess import load_raw_data, clean_data, validate_schema, REQUIRED_COLUMNS, CRITICAL_COLUMNS

@pytest.fixture
def sample_raw_data():
    """Create a sample dataframe mimicking the output of descriptors.py."""
    data = {
        'material_id': ['mp-1', 'mp-2', 'mp-3', 'mp-4', 'mp-5'],
        'formula': ['ABX3', 'ABX3', 'ABX3', 'ABX3', 'ABX3'],
        'structure_type': ['Cubic', 'Cubic', 'Rhombohedral', 'Cubic', 'Cubic'],
        'space_group_number': [221, 221, 161, 221, 221],
        'tolerance_factor': [0.95, 0.85, 1.05, 0.90, np.nan], # One NaN
        'octahedral_factor': [0.45, 0.40, 0.50, 0.42, 0.43],
        'ionic_radius_mismatch': [0.05, 0.10, 0.02, 0.08, 0.04],
        'electronegativity_difference': [0.5, 0.6, 0.3, 0.7, 0.4],
        'decomposition_energy': [-0.2, -0.1, 0.0, -0.3, np.nan] # One NaN
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_col_data():
    """Data missing a required column."""
    data = {
        'material_id': ['mp-1'],
        'formula': ['ABX3'],
        # Missing 'structure_type' and others
        'tolerance_factor': [0.95],
        'decomposition_energy': [-0.2]
    }
    return pd.DataFrame(data)

def test_validate_schema_pass(sample_raw_data):
    is_valid, errors = validate_schema(sample_raw_data)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_schema_missing_columns(missing_col_data):
    is_valid, errors = validate_schema(missing_col_data)
    assert is_valid is False
    assert "Missing required columns" in str(errors[0])

def test_clean_data_removes_nulls(sample_raw_data):
    """Test that clean_data removes rows with NaN in critical columns."""
    # Initial count
    assert len(sample_raw_data) == 5

    # Run clean
    cleaned = clean_data(sample_raw_data)

    # Check that the row with NaN in tolerance_factor AND decomposition_energy is removed
    # In the fixture, mp-5 has NaN in both.
    assert len(cleaned) == 4
    assert not cleaned['tolerance_factor'].isnull().any()
    assert not cleaned['decomposition_energy'].isnull().any()

def test_clean_data_removes_duplicates(sample_raw_data):
    """Test that clean_data removes duplicate material_ids."""
    # Add a duplicate
    df_dup = pd.concat([sample_raw_data, sample_raw_data.iloc[[0]]], ignore_index=True)
    assert len(df_dup) == 6

    cleaned = clean_data(df_dup)
    # The duplicate mp-1 should be removed. The NaN row (mp-5) is also removed.
    # Original unique valid rows: mp-1, mp-2, mp-3, mp-4 (4 rows)
    # Duplicates removed: 1
    # NaN removed: 1
    # Result: 4 rows? Wait.
    # Original: 5 rows.
    # Add duplicate mp-1 -> 6 rows.
    # Drop duplicates -> 5 rows (one mp-1 removed).
    # Drop NaN (mp-5) -> 4 rows.
    assert len(cleaned) == 4
    assert cleaned['material_id'].nunique() == len(cleaned)

def test_clean_data_type_coercion():
    """Test that numeric columns are coerced correctly."""
    data = {
        'material_id': ['mp-1'],
        'formula': ['ABX3'],
        'structure_type': ['Cubic'],
        'space_group_number': [221],
        'tolerance_factor': ['0.95'], # String
        'octahedral_factor': [0.45],
        'ionic_radius_mismatch': [0.05],
        'electronegativity_difference': [0.5],
        'decomposition_energy': ['-0.2'] # String
    }
    df = pd.DataFrame(data)
    cleaned = clean_data(df)
    assert cleaned['tolerance_factor'].dtype in [np.float64, float]
    assert cleaned['decomposition_energy'].dtype in [np.float64, float]
    assert cleaned['tolerance_factor'].iloc[0] == 0.95
    assert cleaned['decomposition_energy'].iloc[0] == -0.2
