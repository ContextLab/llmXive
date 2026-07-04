"""
Unit tests for export_schema_validator module.
Tests schema validation functionality for audit_report.json.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from code.src.audit.export_schema_validator import (
    load_audit_records_from_json,
    validate_audit_report_schema,
    run_schema_validation,
    ERR_SCHEMA_MISSING,
    ERR_SCHEMA_INVALID,
    ERR_FILE_NOT_FOUND,
    ERR_FILE_READ,
)
from code.src.contracts.validation import get_audit_record_validator

class TestLoadAuditRecordsFromJson:
    """Tests for load_audit_records_from_json function."""
    
    def test_load_valid_list(self, tmp_path: Path):
        """Test loading a valid list of records."""
        records = [
            {"id": "1", "is_inconsistent": True},
            {"id": "2", "is_inconsistent": False}
        ]
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        loaded_records, error = load_audit_records_from_json(json_file)
        
        assert error is None
        assert len(loaded_records) == 2
        assert loaded_records[0]["id"] == "1"
    
    def test_load_valid_single_record(self, tmp_path: Path):
        """Test loading a single record wrapped in an object."""
        records = {
            "records": [
                {"id": "1", "is_inconsistent": True}
            ]
        }
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        loaded_records, error = load_audit_records_from_json(json_file)
        
        assert error is None
        assert len(loaded_records) == 1
    
    def test_load_single_record_direct(self, tmp_path: Path):
        """Test loading a single record directly."""
        record = {"id": "1", "is_inconsistent": True}
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(record, f)
        
        loaded_records, error = load_audit_records_from_json(json_file)
        
        assert error is None
        assert len(loaded_records) == 1
        assert loaded_records[0]["id"] == "1"
    
    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading from a non-existent file."""
        json_file = tmp_path / "nonexistent.json"
        
        loaded_records, error = load_audit_records_from_json(json_file)
        
        assert error is not None
        assert ERR_FILE_NOT_FOUND in error
        assert len(loaded_records) == 0
    
    def test_load_invalid_json(self, tmp_path: Path):
        """Test loading invalid JSON."""
        json_file = tmp_path / "invalid.json"
        with open(json_file, 'w') as f:
            f.write("not valid json {")
        
        loaded_records, error = load_audit_records_from_json(json_file)
        
        assert error is not None
        assert ERR_FILE_READ in error
        assert len(loaded_records) == 0

class TestValidateAuditReportSchema:
    """Tests for validate_audit_record_schema function."""
    
    def test_validate_empty_list(self):
        """Test validation of an empty list."""
        is_valid, errors = validate_audit_report_schema([])
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_valid_records(self, tmp_path: Path):
        """Test validation of valid records."""
        # Create a minimal valid schema file for testing
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1", "is_inconsistent": True},
            {"id": "2", "is_inconsistent": False}
        ]
        
        is_valid, errors = validate_audit_report_schema(records, schema_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_invalid_records(self, tmp_path: Path):
        """Test validation of invalid records (missing required field)."""
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1", "is_inconsistent": True},
            {"id": "2"}  # Missing is_inconsistent
        ]
        
        is_valid, errors = validate_audit_report_schema(records, schema_file)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Record 1" in error for error in errors)

class TestRunSchemaValidation:
    """Tests for run_schema_validation function."""
    
    def test_run_validation_success(self, tmp_path: Path):
        """Test successful schema validation."""
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1", "is_inconsistent": True},
            {"id": "2", "is_inconsistent": False}
        ]
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        success, message = run_schema_validation(json_file, schema_file)
        
        assert success is True
        assert "successful" in message.lower()
    
    def test_run_validation_failure(self, tmp_path: Path):
        """Test failed schema validation."""
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1", "is_inconsistent": True},
            {"id": "2"}  # Missing is_inconsistent
        ]
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        success, message = run_schema_validation(json_file, schema_file)
        
        assert success is False
        assert "failed" in message.lower()
    
    def test_run_validation_file_not_found(self, tmp_path: Path):
        """Test validation when file doesn't exist."""
        schema_file = tmp_path / "test_schema.yaml"
        json_file = tmp_path / "nonexistent.json"
        
        success, message = run_schema_validation(json_file, schema_file)
        
        assert success is False
        assert ERR_FILE_NOT_FOUND in message

class TestMainFunction:
    """Tests for the main function."""
    
    def test_main_success(self, tmp_path: Path):
        """Test main function with successful validation."""
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1", "is_inconsistent": True}
        ]
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        with patch('sys.argv', ['export_schema_validator', '--input', str(json_file), '--schema', str(schema_file)]):
            exit_code = main()
        
        assert exit_code == 0
    
    def test_main_failure(self, tmp_path: Path):
        """Test main function with failed validation."""
        schema_content = """
        type: object
        properties:
          id:
            type: string
          is_inconsistent:
            type: boolean
        required:
          - id
          - is_inconsistent
        """
        
        schema_file = tmp_path / "test_schema.yaml"
        with open(schema_file, 'w') as f:
            f.write(schema_content)
        
        records = [
            {"id": "1"}  # Missing is_inconsistent
        ]
        
        json_file = tmp_path / "audit_report.json"
        with open(json_file, 'w') as f:
            json.dump(records, f)
        
        with patch('sys.argv', ['export_schema_validator', '--input', str(json_file), '--schema', str(schema_file)]):
            exit_code = main()
        
        assert exit_code == 1
    
    def test_main_file_not_found(self, tmp_path: Path):
        """Test main function when file doesn't exist."""
        non_existent_file = tmp_path / "nonexistent.json"
        
        with patch('sys.argv', ['export_schema_validator', '--input', str(non_existent_file)]):
            exit_code = main()
        
        assert exit_code == 1

# Import main for testing
from code.src.audit.export_schema_validator import main