"""
Tests for the schema validator module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from utils.schema_validator import (
    load_schema_from_file,
    validate_contract_input,
    validate_file_against_schema,
    FileLoadError,
    InvalidFormatError,
    BEHAVIORAL_TASKS,
    PHASE_TASKS
)

class TestSchemaLoading:
    def test_load_yaml_schema(self):
        """Test loading a valid YAML schema."""
        schema_content = """
        $schema: http://json-schema.org/draft-07/schema#
        type: object
        properties:
          task:
            type: string
        required:
          - task
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(schema_content)
            f_path = Path(f.name)
        
        try:
            schema = load_schema_from_file(f_path)
            assert schema is not None
            assert schema['type'] == 'object'
            assert 'task' in schema['properties']
        finally:
            os.unlink(f_path)
    
    def test_load_missing_schema(self):
        """Test loading a non-existent schema file."""
        with pytest.raises(FileLoadError):
            load_schema_from_file(Path("/nonexistent/path/schema.yaml"))
    
    def test_load_invalid_yaml_schema(self):
        """Test loading an invalid YAML schema."""
        invalid_content = "invalid: yaml: content: ["
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_content)
            f_path = Path(f.name)
        
        try:
            with pytest.raises(FileLoadError):
                load_schema_from_file(f_path)
        finally:
            os.unlink(f_path)

class TestDataValidation:
    def test_valid_behavioral_task(self):
        """Test that valid behavioral tasks pass validation."""
        schema = {
            'properties': {
                'task': {'type': 'string'},
                'onset': {'type': 'number'},
                'duration': {'type': 'number'}
            },
            'required': ['task', 'onset', 'duration']
        }
        
        data = [
            {'task': 'Schandry', 'onset': 0.0, 'duration': 10.0},
            {'task': 'heartbeat', 'onset': 20.0, 'duration': 5.0}
        ]
        
        is_valid, errors = validate_contract_input(data, schema)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_valid_phase_task(self):
        """Test that valid phase tasks pass validation but are flagged."""
        schema = {
            'properties': {
                'task': {'type': 'string'},
                'onset': {'type': 'number'},
                'duration': {'type': 'number'}
            },
            'required': ['task', 'onset', 'duration']
        }
        
        data = [
            {'task': 'TSST', 'onset': 0.0, 'duration': 10.0},
            {'task': 'rest', 'onset': 20.0, 'duration': 5.0},
            {'task': 'baseline', 'onset': 30.0, 'duration': 3.0}
        ]
        
        is_valid, errors = validate_contract_input(data, schema)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_task_value(self):
        """Test that invalid task values are caught."""
        schema = {
            'properties': {
                'task': {'type': 'string'},
                'onset': {'type': 'number'},
                'duration': {'type': 'number'}
            },
            'required': ['task', 'onset', 'duration']
        }
        
        data = [
            {'task': 'invalid_task', 'onset': 0.0, 'duration': 10.0}
        ]
        
        is_valid, errors = validate_contract_input(data, schema)
        assert is_valid is False
        assert len(errors) > 0
        assert any('Invalid task value' in error for error in errors)
    
    def test_missing_required_field(self):
        """Test that missing required fields are caught."""
        schema = {
            'properties': {
                'task': {'type': 'string'},
                'onset': {'type': 'number'},
                'duration': {'type': 'number'}
            },
            'required': ['task', 'onset', 'duration']
        }
        
        data = [
            {'task': 'Schandry', 'onset': 0.0}  # Missing duration
        ]
        
        is_valid, errors = validate_contract_input(data, schema)
        assert is_valid is False
        assert len(errors) > 0
        assert any('Missing required field' in error for error in errors)
    
    def test_numeric_field_validation(self):
        """Test that non-numeric values in numeric fields are caught."""
        schema = {
            'properties': {
                'task': {'type': 'string'},
                'onset': {'type': 'number'},
                'duration': {'type': 'number'}
            },
            'required': ['task', 'onset', 'duration']
        }
        
        data = [
            {'task': 'Schandry', 'onset': 'not_a_number', 'duration': 10.0}
        ]
        
        is_valid, errors = validate_contract_input(data, schema)
        assert is_valid is False
        assert len(errors) > 0
        assert any('must be numeric' in error for error in errors)

class TestFileValidation:
    def test_validate_valid_tsv(self):
        """Test validation of a valid TSV file."""
        schema_content = """
        $schema: http://json-schema.org/draft-07/schema#
        type: object
        properties:
          task:
            type: string
          onset:
            type: number
          duration:
            type: number
        required:
          - task
          - onset
          - duration
        """
        
        tsv_content = "task\tonset\tduration\nSchandry\t0.0\t10.0\nheartbeat\t20.0\t5.0\n"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.yaml"
            tsv_path = Path(tmpdir) / "events.tsv"
            
            with open(schema_path, 'w') as f:
                f.write(schema_content)
            with open(tsv_path, 'w') as f:
                f.write(tsv_content)
            
            is_valid, errors, stats = validate_file_against_schema(tsv_path, schema_path)
            
            assert is_valid is True
            assert len(errors) == 0
            assert stats['total_rows'] == 2
            assert 'schandry' in stats['behavioral_tasks_found']
            assert 'heartbeat' in stats['behavioral_tasks_found']
    
    def test_validate_invalid_tsv(self):
        """Test validation of an invalid TSV file."""
        schema_content = """
        $schema: http://json-schema.org/draft-07/schema#
        type: object
        properties:
          task:
            type: string
          onset:
            type: number
          duration:
            type: number
        required:
          - task
          - onset
          - duration
        """
        
        tsv_content = "task\tonset\tduration\ninvalid_task\t0.0\t10.0\n"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_path = Path(tmpdir) / "schema.yaml"
            tsv_path = Path(tmpdir) / "events.tsv"
            
            with open(schema_path, 'w') as f:
                f.write(schema_content)
            with open(tsv_path, 'w') as f:
                f.write(tsv_content)
            
            is_valid, errors, stats = validate_file_against_schema(tsv_path, schema_path)
            
            assert is_valid is False
            assert len(errors) > 0
            assert stats['total_rows'] == 1
            assert 'invalid_task' in stats['invalid_tasks_found']
    
    def test_validate_missing_file(self):
        """Test validation of a missing TSV file."""
        schema_path = Path("/nonexistent/schema.yaml")
        tsv_path = Path("/nonexistent/events.tsv")
        
        with pytest.raises(FileLoadError):
            validate_file_against_schema(tsv_path, schema_path)