"""
Unit tests for src/cleaning/clean_merge.py

Tests:
- validate_geometry
- enforce_minimum_compositions
- merge_datasets
- add_provenance
- main (integration-ish, mocked)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock, Mock
import logging
import io

# Add src to path if needed, though imports assume relative structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cleaning.clean_merge import (
    validate_geometry,
    enforce_minimum_compositions,
    merge_datasets,
    add_provenance,
    main
)
from src.utils.validation import setup_logger

@pytest.fixture
def sample_structures():
    return pd.DataFrame({
        'structure_id': ['s1', 's2', 's3'],
        'unit_cell_volume': [100.0, 200.0, 150.0],
        'tolerance_factor': [0.95, 1.05, 0.85]
    })

@pytest.fixture
def sample_thermal():
    return pd.DataFrame({
        'structure_id': ['s1', 's2', 's3'],
        'thermal_conductivity': [2.5, 3.0, 1.8],
        'source_reference': ['NIST-123', 'DOI:10.1234/j.abc', 'NIST-456'],
        'temperature': [300, 305, 295]
    })

def test_validate_geometry_positive():
    """Test that valid geometry is kept."""
    df = pd.DataFrame({
        'unit_cell_volume': [100.0, 200.0],
        'tolerance_factor': [0.9, 1.0]
    })
    result = validate_geometry(df)
    assert len(result) == 2

def test_validate_geometry_negative_volume():
    """Test that negative volume is removed."""
    df = pd.DataFrame({
        'unit_cell_volume': [100.0, -50.0],
        'tolerance_factor': [0.9, 0.9]
    })
    result = validate_geometry(df)
    assert len(result) == 1

def test_validate_geometry_tolerance_out_of_range():
    """Test that tolerance factor outside [0.8, 1.1] is removed."""
    df = pd.DataFrame({
        'unit_cell_volume': [100.0, 200.0, 300.0],
        'tolerance_factor': [0.9, 1.2, 0.7]
    })
    result = validate_geometry(df)
    assert len(result) == 1

def test_enforce_minimum_compositions_pass():
    """Test that sufficient samples pass."""
    df = pd.DataFrame({
        'structure_id': [f's{i}' for i in range(60)],
        'val': [1]*60
    })
    # Should not raise
    result = enforce_minimum_compositions(df, min_count=50)
    assert len(result) == 60

def test_enforce_minimum_compositions_fail():
    """Test that insufficient samples raise SystemExit."""
    df = pd.DataFrame({
        'structure_id': [f's{i}' for i in range(40)],
        'val': [1]*40
    })
    with pytest.raises(SystemExit) as excinfo:
        enforce_minimum_compositions(df, min_count=50)
    assert "Insufficient samples" in str(excinfo.value)

def test_merge_datasets():
    """Test merging on structure_id."""
    s_df = pd.DataFrame({'structure_id': ['a', 'b'], 'vol': [1, 2]})
    t_df = pd.DataFrame({'structure_id': ['a', 'b'], 'k': [10, 20]})
    result = merge_datasets(s_df, t_df)
    assert len(result) == 2
    assert 'vol' in result.columns
    assert 'k' in result.columns

def test_merge_datasets_no_match():
    """Test merging with no common IDs."""
    s_df = pd.DataFrame({'structure_id': ['a'], 'vol': [1]})
    t_df = pd.DataFrame({'structure_id': ['b'], 'k': [10]})
    result = merge_datasets(s_df, t_df)
    assert len(result) == 0

def test_add_provenance():
    """Test adding provenance validity column."""
    df = pd.DataFrame({
        'structure_id': ['s1', 's2'],
        'source_reference': ['NIST-123', 'Invalid']
    })
    # Mock is_valid_source_reference to return True/False based on NIST prefix
    # Since we can't easily import the function without circular deps in test,
    # we rely on the logic inside clean_merge which calls is_valid_source_reference.
    # For this unit test, we assume the function exists and works as expected in the module.
    # We will just check the column is added.
    # Note: In a real scenario, we'd mock the import.
    # Here we just verify the function runs and adds the column.
    
    # We need to mock the is_valid_source_reference from cleaning.provenance_validator
    # to avoid dependency issues in this unit test context if the validator is complex.
    # But since the task is to test clean_merge, and clean_merge imports it,
    # we assume the import works.
    
    # Let's create a simple mock for the function used inside
    with patch('src.cleaning.clean_merge.is_valid_source_reference') as mock_valid:
        mock_valid.side_effect = lambda x: x.startswith('NIST')
        result = add_provenance(df)
        assert 'provenance_valid' in result.columns
        assert result.loc[0, 'provenance_valid'] == True
        assert result.loc[1, 'provenance_valid'] == False

@patch('src.cleaning.clean_merge.fetch_perovskite_structures')
@patch('src.cleaning.clean_merge.fetch_perovskite_thermal_data')
@patch('src.cleaning.clean_merge.filter_valid_provenance')
@patch('src.cleaning.clean_merge.apply_temperature_normalization')
@patch('src.cleaning.clean_merge.validate_no_nulls')
@patch('src.cleaning.clean_merge.validate_geometry')
@patch('src.cleaning.clean_merge.enforce_minimum_compositions')
@patch('src.cleaning.clean_merge.validate_environment')
def test_main_flow(
    mock_env,
    mock_enforce,
    mock_geom,
    mock_nulls,
    mock_norm,
    mock_filter,
    mock_thermal_fetch,
    mock_struct_fetch
):
    """Test the main function flow with mocked dependencies."""
    mock_env.return_value = None
    mock_struct_fetch.return_value = pd.DataFrame({'structure_id': ['s1'], 'unit_cell_volume': [100], 'tolerance_factor': [0.9]})
    mock_thermal_fetch.return_value = pd.DataFrame({'structure_id': ['s1'], 'thermal_conductivity': [2.0], 'source_reference': ['NIST-1'], 'temperature': [300]})
    mock_filter.return_value = (mock_thermal_fetch.return_value, {})
    mock_norm.return_value = mock_thermal_fetch.return_value
    mock_nulls.return_value = mock_thermal_fetch.return_value
    mock_geom.return_value = mock_thermal_fetch.return_value
    mock_enforce.return_value = mock_thermal_fetch.return_value

    # Run main
    main([])

    # Verify calls
    mock_struct_fetch.assert_called_once()
    mock_thermal_fetch.assert_called_once()
    mock_enforce.assert_called_once()
    
    # Check output file creation (side effect of to_csv)
    # We can't easily check file existence in a unit test without mocking Path,
    # but we verified the logic flow.