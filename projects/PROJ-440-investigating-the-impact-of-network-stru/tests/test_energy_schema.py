"""
Tests for the energy decay schema and validation logic.
"""
import pytest
import yaml
import csv
import tempfile
import os
from pathlib import Path
from code.utils.energy_schema_loader import load_energy_schema, validate_csv_against_schema


class TestEnergySchemaLoading:
    """Tests for schema loading functionality."""

    def test_load_schema_success(self):
        """Test that the schema can be loaded successfully."""
        schema = load_energy_schema()
        assert schema is not None
        assert 'properties' in schema
        assert 'required' in schema
        assert 'graph_id' in schema['properties']
        assert 'decay_rate' in schema['properties']
        assert 'r_squared' in schema['properties']
        assert 'status' in schema['properties']

    def test_schema_has_required_fields(self):
        """Test that the schema defines all required fields."""
        schema = load_energy_schema()
        required_fields = schema.get('required', [])
        assert 'graph_id' in required_fields
        assert 'decay_rate' in required_fields
        assert 'r_squared' in required_fields
        assert 'status' in required_fields

    def test_schema_has_enum_constraints(self):
        """Test that the status field has proper enum constraints."""
        schema = load_energy_schema()
        status_def = schema['properties']['status']
        assert 'enum' in status_def
        assert 'dissipative' in status_def['enum']
        assert 'resonant' in status_def['enum']
        assert 'unstable' in status_def['enum']
        assert 'failed' in status_def['enum']


class TestCSVValidation:
    """Tests for CSV validation against the schema."""

    def test_validate_valid_csv(self):
        """Test validation of a properly formatted CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'r_squared', 'status'])
            writer.writerow(['graph_001', '0.05', '0.98', 'dissipative'])
            writer.writerow(['graph_002', '0.03', '0.96', 'dissipative'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'status'])  # Missing r_squared
            writer.writerow(['graph_001', '0.05', 'dissipative'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert any('r_squared' in error for error in errors)
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_enum_value(self):
        """Test validation fails for invalid status value."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'r_squared', 'status'])
            writer.writerow(['graph_001', '0.05', '0.98', 'invalid_status'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert any('invalid_status' in error for error in errors)
        finally:
            os.unlink(temp_path)

    def test_validate_file_not_found(self):
        """Test validation fails for non-existent file."""
        is_valid, errors = validate_csv_against_schema('/nonexistent/path.csv')
        assert not is_valid
        assert any('not found' in error.lower() for error in errors)

    def test_validate_empty_csv(self):
        """Test validation fails for empty CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('')
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert any('empty' in error.lower() for error in errors)
        finally:
            os.unlink(temp_path)

    def test_validate_non_numeric_value(self):
        """Test validation fails for non-numeric values in numeric fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'r_squared', 'status'])
            writer.writerow(['graph_001', 'not_a_number', '0.98', 'dissipative'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert not is_valid
            assert any('not_a_number' in error for error in errors)
        finally:
            os.unlink(temp_path)

    def test_validate_resonant_status(self):
        """Test validation accepts resonant status."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'r_squared', 'status'])
            writer.writerow(['graph_001', '-0.02', '0.97', 'resonant'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_unstable_status(self):
        """Test validation accepts unstable status."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['graph_id', 'decay_rate', 'r_squared', 'status', 'convergence_std', 'convergence_mean'])
            writer.writerow(['graph_001', '0.05', '0.98', 'unstable', '0.015', '0.05'])
            temp_path = f.name

        try:
            is_valid, errors = validate_csv_against_schema(temp_path)
            assert is_valid
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)