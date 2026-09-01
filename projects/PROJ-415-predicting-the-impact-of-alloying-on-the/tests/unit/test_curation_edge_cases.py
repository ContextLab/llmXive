"""
Unit tests for edge cases in data curation (T039).
Tests missing atomic data and single host metal scenarios.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import logging

# Import the functions under test
# Note: Using relative imports adjusted for execution context if run as script,
# but standard project imports are preferred.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.curation import (
    validate_atomic_radii,
    exclude_missing_concentration,
    log_exclusions,
    run_curation
)
from utils.constants import get_metallic_radius

@pytest.fixture
def sample_df():
    """Create a sample DataFrame mimicking the curated data structure."""
    return pd.DataFrame({
        'solute_symbol': ['Cu', 'Ni', 'Zn', 'Au'],
        'host_symbol': ['Al', 'Al', 'Al', 'Al'],
        'concentration': [5.0, 10.0, None, 15.0],
        'activation_energy': [1.2, 1.3, 1.4, 1.5],
        'crystal_structure': ['FCC', 'FCC', 'FCC', 'FCC'],
        'diffusion_mode': ['self', 'self', 'self', 'self']
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_validate_atomic_radii_missing_symbol(sample_df):
    """Test that validate_atomic_radii correctly identifies missing atomic data."""
    # Introduce a symbol not in our constants (simulating missing data)
    df_missing = sample_df.copy()
    df_missing.loc[0, 'solute_symbol'] = 'Unk'  # Unknown element

    missing_radii, missing_elements = validate_atomic_radii(df_missing)

    assert len(missing_elements) > 0
    assert 'Unk' in missing_elements
    assert len(missing_radii) == 1

def test_exclude_missing_concentration(sample_df):
    """Test that exclude_missing_concentration removes rows with None/NaN concentration."""
    filtered_df, excluded_rows = exclude_missing_concentration(sample_df)

    # Original has 4 rows, 1 has None concentration
    assert len(filtered_df) == 3
    assert len(excluded_rows) == 1
    assert excluded_rows.iloc[0]['row_id'] == 2  # Index 2 had None concentration

def test_log_exclusions_format(sample_df, temp_dir):
    """Test that log_exclusions writes the correct CSV format with count header."""
    exclusions = pd.DataFrame({
        'row_id': [0, 1],
        'reason_code': ['MISSING_CONCENTRATION', 'MISSING_RADIUS']
    })

    log_path = temp_dir / "exclusions.log"
    log_exclusions(exclusions, str(log_path))

    assert log_path.exists()
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    # First line must be the count comment
    assert lines[0].startswith('# EXCLUSION_COUNT:')
    assert '2' in lines[0]
    
    # Subsequent lines should be CSV data
    assert 'row_id' in lines[1]
    assert 'MISSING_CONCENTRATION' in lines[2]

def test_run_curation_missing_atomic_data(sample_df, temp_dir):
    """
    Test the full curation pipeline when atomic data is missing.
    Ensures errors/missing_atomic_data.csv is created.
    """
    # Create a DataFrame with missing atomic radii
    df_missing = sample_df.copy()
    df_missing.loc[0, 'solute_symbol'] = 'Xx' # Fake element

    input_path = temp_dir / "input.csv"
    output_path = temp_dir / "output.csv"
    errors_dir = temp_dir / "errors"
    errors_dir.mkdir()
    logs_dir = temp_dir / "logs"
    logs_dir.mkdir()

    df_missing.to_csv(input_path, index=False)

    # Run curation
    final_df, exclusion_log_path, errors_log_path = run_curation(
        input_path=str(input_path),
        output_path=str(output_path),
        errors_dir=str(errors_dir),
        logs_dir=str(logs_dir)
    )

    # Verify output exists
    assert os.path.exists(output_path)
    assert os.path.exists(exclusion_log_path)

    # Verify errors file is created if missing data exists
    assert os.path.exists(errors_log_path)
    
    # Verify the content of the errors file
    with open(errors_log_path, 'r') as f:
        content = f.read()
        assert 'Xx' in content
        assert 'missing_attribute' in content or 'solute_symbol' in content

def test_single_host_metal_warning_handling():
    """
    Test that the system handles single-host-metal datasets gracefully.
    This test verifies the logic that would trigger the warning in ingestion,
    but here we verify the curation logic doesn't crash on uniform host data.
    """
    # Create a dataset with only one host metal
    single_host_df = pd.DataFrame({
        'solute_symbol': ['Cu', 'Ni', 'Zn'],
        'host_symbol': ['Al', 'Al', 'Al'],  # Only Al
        'concentration': [5.0, 10.0, 15.0],
        'activation_energy': [1.2, 1.3, 1.4],
        'crystal_structure': ['FCC', 'FCC', 'FCC'],
        'diffusion_mode': ['self', 'self', 'self']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        errors_dir = Path(tmpdir) / "errors"
        errors_dir.mkdir()
        logs_dir = Path(tmpdir) / "logs"
        logs_dir.mkdir()

        single_host_df.to_csv(input_path, index=False)

        # Should not raise an exception
        final_df, _, _ = run_curation(
            input_path=str(input_path),
            output_path=str(output_path),
            errors_dir=str(errors_dir),
            logs_dir=str(logs_dir)
        )

        # Should return the data (minus any missing values)
        assert len(final_df) > 0
        assert all(final_df['host_symbol'] == 'Al')

def test_get_metallic_radius_known_element():
    """Verify that get_metallic_radius returns a value for a known element."""
    radius = get_metallic_radius('Cu')
    assert radius is not None
    assert isinstance(radius, float)
    assert radius > 0

def test_get_metallic_radius_unknown_element():
    """Verify that get_metallic_radius returns None for an unknown element."""
    radius = get_metallic_radius('FakeElementX')
    assert radius is None