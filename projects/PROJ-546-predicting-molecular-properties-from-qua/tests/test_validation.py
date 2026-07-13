"""
Unit tests for validation utilities.
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.validation_utils import (
    validate_columns, 
    validate_physical_ranges, 
    validate_data_types, 
    validate_full,
    ValidationError,
    REQUIRED_COLUMNS
)


def create_temp_csv(rows, header=None):
    """Helper to create a temporary CSV file with given rows."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    with os.fdopen(fd, 'w', newline='') as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        for row in rows:
            writer.writerow(row)
    return Path(path)


class TestValidateColumns:
    def test_all_columns_present(self):
        """Test that validation passes when all required columns are present."""
        header = REQUIRED_COLUMNS + ['extra_column']
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, missing = validate_columns(filepath)
            assert is_valid
            assert len(missing) == 0
        finally:
            filepath.unlink()

    def test_missing_column(self):
        """Test that validation fails when a required column is missing."""
        header = [col for col in REQUIRED_COLUMNS if col != 'homo']
        rows = [
            ['CCO', 'mol1', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, missing = validate_columns(filepath)
            assert not is_valid
            assert 'homo' in missing
        finally:
            filepath.unlink()

    def test_file_not_exists(self):
        """Test that ValidationError is raised for non-existent file."""
        with pytest.raises(ValidationError):
            validate_columns(Path('/nonexistent/path.csv'))

class TestValidatePhysicalRanges:
    def test_valid_ranges(self):
        """Test validation passes for physically reasonable values."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '0.0', 'success'],
            ['CN', 'mol2', '-8.0', '-3.0', '1.0', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_physical_ranges(filepath)
            assert is_valid
            assert len(errors) == 0
        finally:
            filepath.unlink()

    def test_homo_greater_than_lumo(self):
        """Test validation fails when HOMO >= LUMO."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-5.0', '-10.0', '1.5', '0.0', 'success']  # HOMO > LUMO
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_physical_ranges(filepath)
            assert not is_valid
            assert any('HOMO' in err and 'LUMO' in err for err in errors)
        finally:
            filepath.unlink()

    def test_charge_out_of_bounds(self):
        """Test validation fails when charge is outside reasonable bounds."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '15.0', 'success']  # Charge > 10
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_physical_ranges(filepath)
            assert not is_valid
            assert any('charge' in err.lower() for err in errors)
        finally:
            filepath.unlink()

    def test_nan_values(self):
        """Test validation fails for NaN values."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', 'nan', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_physical_ranges(filepath)
            assert not is_valid
            assert any('NaN' in err for err in errors)
        finally:
            filepath.unlink()

class TestValidateDataTypes:
    def test_valid_types(self):
        """Test validation passes for correct data types."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_data_types(filepath)
            assert is_valid
            assert len(errors) == 0
        finally:
            filepath.unlink()

    def test_invalid_float(self):
        """Test validation fails for non-numeric values in float columns."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', 'not_a_number', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_data_types(filepath)
            assert not is_valid
            assert any('not a valid float' in err for err in errors)
        finally:
            filepath.unlink()

    def test_negative_mayer_bond_order(self):
        """Test validation fails for negative Mayer bond order."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '-1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_data_types(filepath)
            assert not is_valid
            assert any('negative' in err for err in errors)
        finally:
            filepath.unlink()

    def test_invalid_convergence_status(self):
        """Test validation fails for invalid convergence status."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '0.0', 'invalid_status']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            is_valid, errors = validate_data_types(filepath)
            assert not is_valid
            assert any('Invalid convergence_status' in err for err in errors)
        finally:
            filepath.unlink()

class TestValidateFull:
    def test_full_validation_passes(self):
        """Test full validation passes for a valid file."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-10.5', '-5.2', '1.5', '0.0', 'success']
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            assert validate_full(filepath)
        finally:
            filepath.unlink()

    def test_full_validation_fails(self):
        """Test full validation fails for an invalid file."""
        header = REQUIRED_COLUMNS
        rows = [
            ['CCO', 'mol1', '-5.0', '-10.0', '1.5', '0.0', 'success']  # HOMO > LUMO
        ]
        filepath = create_temp_csv(rows, header)
        
        try:
            with pytest.raises(ValidationError):
                validate_full(filepath)
        finally:
            filepath.unlink()