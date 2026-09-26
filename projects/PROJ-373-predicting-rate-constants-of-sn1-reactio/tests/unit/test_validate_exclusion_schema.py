import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.validate_exclusion_schema import validate_row, validate_exclusion_log, load_schema

class TestValidateRow:
    """Unit tests for the validate_row function."""

    def test_valid_row(self):
        """Test that a valid row passes validation."""
        schema = {
            'fields': [
                {'name': 'row_index', 'type': 'integer'},
                {'name': 'reason', 'type': 'string'},
                {'name': 'original_smiles', 'type': 'string'}
            ]
        }
        row = {
            'row_index': '123',
            'reason': 'primary_substrate_filter',
            'original_smiles': 'CC(C)(C)Br'
        }
        assert validate_row(row, schema) is None

    def test_missing_row_index(self):
        """Test that a row missing row_index fails validation."""
        schema = {}
        row = {
            'reason': 'primary_substrate_filter',
            'original_smiles': 'CC(C)(C)Br'
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'row_index' in error

    def test_missing_reason(self):
        """Test that a row missing reason fails validation."""
        schema = {}
        row = {
            'row_index': '123',
            'original_smiles': 'CC(C)(C)Br'
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'reason' in error

    def test_missing_smiles(self):
        """Test that a row missing original_smiles fails validation."""
        schema = {}
        row = {
            'row_index': '123',
            'reason': 'primary_substrate_filter'
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'original_smiles' in error

    def test_invalid_row_index_type(self):
        """Test that a non-integer row_index fails validation."""
        schema = {}
        row = {
            'row_index': 'not_a_number',
            'reason': 'primary_substrate_filter',
            'original_smiles': 'CC(C)(C)Br'
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'integer' in error

    def test_empty_reason(self):
        """Test that an empty reason fails validation."""
        schema = {}
        row = {
            'row_index': '123',
            'reason': '',
            'original_smiles': 'CC(C)(C)Br'
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'empty' in error

    def test_empty_smiles(self):
        """Test that an empty original_smiles fails validation."""
        schema = {}
        row = {
            'row_index': '123',
            'reason': 'primary_substrate_filter',
            'original_smiles': ''
        }
        error = validate_row(row, schema)
        assert error is not None
        assert 'empty' in error

class TestValidateExclusionLog:
    """Integration tests for the validate_exclusion_log function."""

    @pytest.fixture
    def temp_schema_file(self, tmp_path):
        """Create a temporary schema file."""
        schema = {
            'fields': [
                {'name': 'row_index', 'type': 'integer'},
                {'name': 'reason', 'type': 'string'},
                {'name': 'original_smiles', 'type': 'string'}
            ]
        }
        schema_path = tmp_path / 'schema.yaml'
        with open(schema_path, 'w') as f:
            yaml.dump(schema, f)
        return schema_path

    @pytest.fixture
    def valid_log_file(self, tmp_path):
        """Create a temporary valid exclusion log."""
        log_path = tmp_path / 'valid_log.csv'
        with open(log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['row_index', 'reason', 'original_smiles'])
            writer.writeheader()
            writer.writerow({
                'row_index': '1',
                'reason': 'primary_substrate_filter',
                'original_smiles': 'CC(C)(C)Br'
            })
            writer.writerow({
                'row_index': '2',
                'reason': 'ambiguous_stereochemistry',
                'original_smiles': 'C[C@H](O)Cl'
            })
        return log_path

    @pytest.fixture
    def invalid_log_file(self, tmp_path):
        """Create a temporary invalid exclusion log."""
        log_path = tmp_path / 'invalid_log.csv'
        with open(log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['row_index', 'reason', 'original_smiles'])
            writer.writeheader()
            writer.writerow({
                'row_index': '1',
                'reason': 'primary_substrate_filter',
                'original_smiles': 'CC(C)(C)Br'
            })
            writer.writerow({
                'row_index': 'not_a_number',
                'reason': 'descriptor_failure',
                'original_smiles': 'C[C@H](O)Cl'
            })
        return log_path

    def test_validate_valid_log(self, tmp_path, temp_schema_file, valid_log_file):
        """Test validation of a fully valid log."""
        output_path = tmp_path / 'validation_report.csv'
        
        # Mock logger
        import logging
        logger = logging.getLogger("test")
        
        success = validate_exclusion_log(valid_log_file, temp_schema_file, output_path, logger)
        
        assert success is True
        assert output_path.exists()

    def test_validate_invalid_log(self, tmp_path, temp_schema_file, invalid_log_file):
        """Test validation of a log with invalid rows."""
        output_path = tmp_path / 'validation_report.csv'
        
        import logging
        logger = logging.getLogger("test")
        
        success = validate_exclusion_log(invalid_log_file, temp_schema_file, output_path, logger)
        
        assert success is False
        assert output_path.exists()
        
        # Check that the report contains the error
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 2  # Summary + at least one error
            assert any(row['validation_status'] == 'INVALID' for row in rows)

    def test_missing_input_file(self, tmp_path, temp_schema_file):
        """Test validation when input file is missing."""
        input_path = tmp_path / 'nonexistent.csv'
        output_path = tmp_path / 'validation_report.csv'
        
        import logging
        logger = logging.getLogger("test")
        
        success = validate_exclusion_log(input_path, temp_schema_file, output_path, logger)
        
        assert success is False

    def test_missing_schema_file(self, tmp_path, valid_log_file):
        """Test validation when schema file is missing."""
        schema_path = tmp_path / 'nonexistent_schema.yaml'
        output_path = tmp_path / 'validation_report.csv'
        
        import logging
        logger = logging.getLogger("test")
        
        with pytest.raises(FileNotFoundError):
            validate_exclusion_log(valid_log_file, schema_path, output_path, logger)