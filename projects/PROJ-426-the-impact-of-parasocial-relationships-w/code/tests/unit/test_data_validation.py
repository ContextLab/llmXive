"""
Unit tests for data validation utilities.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import hashlib

from src.utils.data_validation import (
    ValidationError,
    compute_sha256,
    load_schema,
    validate_field_type,
    validate_record,
    validate_parquet_schema,
    validate_csv_schema,
    record_checksum,
    validate_and_checksum
)


class TestComputeSha256:
    """Tests for compute_sha256 function."""
    
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test computing SHA256 of a valid file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_sha256(test_file)
        expected = hashlib.sha256(test_content).hexdigest()
        
        assert checksum == expected
        
    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for nonexistent file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(nonexistent)


class TestLoadSchema:
    """Tests for load_schema function."""
    
    def test_load_valid_schema(self, tmp_path):
        """Test loading a valid YAML schema."""
        schema_content = {
            'name': 'test_schema',
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
            
        loaded = load_schema(schema_file)
        
        assert loaded['name'] == 'test_schema'
        assert 'id' in loaded['fields']
        assert loaded['fields']['id']['type'] == 'integer'
        
    def test_load_schema_missing_fields(self, tmp_path):
        """Test that ValidationError is raised for schema without 'fields'."""
        schema_content = {'name': 'test_schema'}
        
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema_content, f)
            
        with pytest.raises(ValidationError):
            load_schema(schema_file)
            
    def test_load_nonexistent_schema(self, tmp_path):
        """Test that FileNotFoundError is raised for nonexistent schema."""
        with pytest.raises(FileNotFoundError):
            load_schema(tmp_path / "nonexistent.yaml")


class TestValidateFieldType:
    """Tests for validate_field_type function."""
    
    def test_validate_string(self):
        """Test string type validation."""
        assert validate_field_type("hello", "string") is True
        assert validate_field_type(None, "string") is True
        assert validate_field_type(123, "string") is False
        
    def test_validate_integer(self):
        """Test integer type validation."""
        assert validate_field_type(42, "integer") is True
        assert validate_field_type(np.int64(42), "integer") is True
        assert validate_field_type(None, "integer") is True
        assert validate_field_type("42", "integer") is False
        assert validate_field_type(3.14, "integer") is False
        
    def test_validate_float(self):
        """Test float type validation."""
        assert validate_field_type(3.14, "float") is True
        assert validate_field_type(np.float64(3.14), "float") is True
        assert validate_field_type(None, "float") is True
        assert validate_field_type("3.14", "float") is False
        
    def test_validate_boolean(self):
        """Test boolean type validation."""
        assert validate_field_type(True, "boolean") is True
        assert validate_field_type(np.bool_(True), "boolean") is True
        assert validate_field_type(None, "boolean") is True
        assert validate_field_type(1, "boolean") is False


class TestValidateRecord:
    """Tests for validate_record function."""
    
    def test_valid_record(self):
        """Test validation of a valid record."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        record = {'id': 1, 'name': 'Alice'}
        
        errors = validate_record(record, schema)
        assert errors == []
        
    def test_missing_required_field(self):
        """Test validation with missing required field."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        record = {'id': 1}
        
        errors = validate_record(record, schema)
        assert len(errors) == 1
        assert 'Missing required field: name' in errors[0]
        
    def test_invalid_type(self):
        """Test validation with invalid field type."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True}
            }
        }
        record = {'id': 'not_an_integer'}
        
        errors = validate_record(record, schema)
        assert len(errors) == 1
        assert 'invalid type' in errors[0]
        
    def test_value_constraint_violation(self):
        """Test validation with min/max constraint violation."""
        schema = {
            'fields': {
                'age': {'type': 'integer', 'required': True, 'min': 0, 'max': 150}
            }
        }
        record = {'age': 200}
        
        errors = validate_record(record, schema)
        assert len(errors) == 1
        assert 'above maximum' in errors[0]


class TestValidateParquetSchema:
    """Tests for validate_parquet_schema function."""
    
    def test_valid_parquet_schema(self, tmp_path):
        """Test validation of a valid Parquet DataFrame."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
        
        is_valid, errors = validate_parquet_schema(df, schema)
        assert is_valid is True
        assert errors == []
        
    def test_missing_required_column(self):
        """Test validation with missing required column."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        df = pd.DataFrame({'id': [1, 2]})
        
        is_valid, errors = validate_parquet_schema(df, schema)
        assert is_valid is False
        assert any('Missing required column: name' in e for e in errors)
        
    def test_strict_mode_extra_columns(self):
        """Test strict mode with extra columns."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True}
            }
        }
        df = pd.DataFrame({'id': [1, 2], 'extra': ['a', 'b']})
        
        is_valid, errors = validate_parquet_schema(df, schema, strict=True)
        assert is_valid is False
        assert any('Extra columns' in e for e in errors)


class TestValidateCsvSchema:
    """Tests for validate_csv_schema function."""
    
    def test_valid_csv_schema(self, tmp_path):
        """Test validation of a valid CSV DataFrame."""
        schema = {
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
        
        is_valid, errors = validate_csv_schema(df, schema)
        assert is_valid is True
        assert errors == []


class TestRecordChecksum:
    """Tests for record_checksum function."""
    
    def test_record_checksum_success(self, tmp_path):
        """Test successful checksum recording."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum_file = tmp_path / "checksums" / "test.txt.sha256"
        
        checksum = record_checksum(test_file, checksum_file)
        
        assert checksum is not None
        assert checksum_file.exists()
        
        # Verify checksum content
        with open(checksum_file, 'r') as f:
            content = f.read()
            
        assert checksum in content
        assert 'algorithm: sha256' in content
        
    def test_record_checksum_creates_directory(self, tmp_path):
        """Test that checksum recording creates parent directories."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello")
        
        checksum_file = tmp_path / "deep" / "nested" / "dir" / "checksum.txt.sha256"
        
        record_checksum(test_file, checksum_file)
        
        assert checksum_file.exists()


class TestValidateAndChecksum:
    """Tests for validate_and_checksum function."""
    
    def test_validate_and_checksum_success(self, tmp_path):
        """Test successful validation and checksum recording."""
        # Create schema
        schema = {
            'name': 'test',
            'fields': {
                'id': {'type': 'integer', 'required': True}
            }
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
            
        # Create data file
        df = pd.DataFrame({'id': [1, 2, 3]})
        data_file = tmp_path / "data.parquet"
        df.to_parquet(data_file)
        
        # Create checksum file path
        checksum_file = tmp_path / "checksum.txt.sha256"
        
        result = validate_and_checksum(
            data_file,
            schema_path=schema_file,
            checksum_path=checksum_file,
            file_type='parquet'
        )
        
        assert result['is_valid'] is True
        assert result['checksum'] is not None
        assert result['checksum_path'] == str(checksum_file)
        assert len(result['validation_errors']) == 0
        
    def test_validate_and_checksum_fails_validation(self, tmp_path):
        """Test validation failure is properly reported."""
        # Create schema with required field
        schema = {
            'name': 'test',
            'fields': {
                'id': {'type': 'integer', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, 'w') as f:
            yaml.dump(schema, f)
            
        # Create data file missing required field
        df = pd.DataFrame({'id': [1, 2, 3]})
        data_file = tmp_path / "data.parquet"
        df.to_parquet(data_file)
        
        with pytest.raises(ValidationError):
            validate_and_checksum(
                data_file,
                schema_path=schema_file,
                file_type='parquet'
            )