"""
Unit tests for validation utilities.
"""

import csv
import os
import tempfile
from pathlib import Path
import pytest

from utils.validation_utils import (
    ValidationError,
    validate_columns,
    validate_physical_ranges,
    validate_data_types,
    validate_full
)

# Test fixtures
@pytest.fixture
def valid_csv_file():
    """Create a temporary valid CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge'])
        writer.writerow(['CCO', '-10.5', '-1.2', '[0.1, -0.2, 0.1, -0.0]', '0.0'])
        writer.writerow(['CC(=O)O', '-11.0', '-0.8', '[0.2, -0.3, 0.1, 0.0]', '0.0'])
        temp_path = f.name
    
    yield Path(temp_path)
    
    os.unlink(temp_path)

@pytest.fixture
def invalid_homo_lumo_csv():
    """Create a CSV where HOMO >= LUMO."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge'])
        writer.writerow(['CCO', '-5.0', '-6.0', '[0.1, -0.2, 0.1, -0.0]', '0.0'])  # HOMO > LUMO
        temp_path = f.name
    
    yield Path(temp_path)
    
    os.unlink(temp_path)

@pytest.fixture
def invalid_charge_sum_csv():
    """Create a CSV where charge sum doesn't match net charge."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge'])
        writer.writerow(['CCO', '-10.5', '-1.2', '[1.0, -2.0, 3.0, -4.0]', '0.0'])  # Sum = -2.0 != 0.0
        temp_path = f.name
    
    yield Path(temp_path)
    
    os.unlink(temp_path)

@pytest.fixture
def missing_column_csv():
    """Create a CSV missing required columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV'])  # Missing LUMO_eV, mulliken_charges, net_charge
        writer.writerow(['CCO', '-10.5'])
        temp_path = f.name
    
    yield Path(temp_path)
    
    os.unlink(temp_path)

@pytest.fixture
def invalid_type_csv():
    """Create a CSV with invalid data types."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge'])
        writer.writerow(['CCO', 'not_a_number', '-1.2', '[0.1, -0.2]', '0.0'])
        temp_path = f.name
    
    yield Path(temp_path)
    
    os.unlink(temp_path)

# Tests for validate_columns
def test_validate_columns_valid(valid_csv_file):
    is_valid, missing = validate_columns(valid_csv_file, ['SMILES', 'HOMO_eV', 'LUMO_eV'])
    assert is_valid
    assert len(missing) == 0

def test_validate_columns_missing(missing_column_csv):
    is_valid, missing = validate_columns(
        missing_column_csv, 
        ['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge']
    )
    assert not is_valid
    assert 'LUMO_eV' in missing
    assert 'mulliken_charges' in missing
    assert 'net_charge' in missing

def test_validate_columns_file_not_found():
    with pytest.raises(ValidationError):
        validate_columns(Path('/nonexistent/file.csv'), ['SMILES'])

# Tests for validate_physical_ranges
def test_validate_physical_ranges_valid(valid_csv_file):
    is_valid, errors = validate_physical_ranges(valid_csv_file)
    assert is_valid
    assert len(errors) == 0

def test_validate_physical_ranges_homo_lumo(invalid_homo_lumo_csv):
    is_valid, errors = validate_physical_ranges(invalid_homo_lumo_csv)
    assert not is_valid
    assert any('HOMO' in e and 'LUMO' in e for e in errors)

def test_validate_physical_ranges_charge_sum(invalid_charge_sum_csv):
    is_valid, errors = validate_physical_ranges(invalid_charge_sum_csv)
    assert not is_valid
    assert any('Mulliken' in e and 'net charge' in e for e in errors)

# Tests for validate_data_types
def test_validate_data_types_valid(valid_csv_file):
    is_valid, errors = validate_data_types(valid_csv_file)
    assert is_valid
    assert len(errors) == 0

def test_validate_data_types_invalid(invalid_type_csv):
    is_valid, errors = validate_data_types(invalid_type_csv)
    assert not is_valid
    assert any('not_a_number' in e for e in errors)

# Tests for validate_full
def test_validate_full_valid(valid_csv_file):
    is_valid, errors = validate_full(valid_csv_file)
    assert is_valid
    assert len(errors) == 0

def test_validate_full_multiple_errors(invalid_homo_lumo_csv):
    is_valid, errors = validate_full(invalid_homo_lumo_csv)
    assert not is_valid
    assert len(errors) > 0

def test_validate_full_missing_columns(missing_column_csv):
    is_valid, errors = validate_full(missing_column_csv)
    assert not is_valid
    assert any('Column error' in e for e in errors)

# Edge cases
def test_validate_empty_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('')
        temp_path = f.name
    
    try:
        with pytest.raises(ValidationError):
            validate_columns(Path(temp_path), ['SMILES'])
    finally:
        os.unlink(temp_path)

def test_validate_charge_sum_tolerance():
    """Test that small floating point differences are tolerated."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge'])
        # Sum is 0.00001, net_charge is 0.0 - should pass within 0.01 tolerance
        writer.writerow(['CCO', '-10.5', '-1.2', '[0.5, 0.5, -1.0, 0.00001]', '0.0'])
        temp_path = f.name
    
    try:
        is_valid, errors = validate_physical_ranges(Path(temp_path))
        assert is_valid
        assert len(errors) == 0
    finally:
        os.unlink(temp_path)
