"""
Unit tests for data_validation module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

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
    def test_compute_sha256_valid_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, World!")
        
        checksum = compute_sha256(file_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    
    def test_compute_sha256_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")


class TestLoadSchema:
    def test_load_schema_valid(self, tmp_path):
        schema_content = """
        fields:
          name:
            type: string
          age:
            type: int
        required:
          - name
        """
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text(schema_content)
        
        schema = load_schema(schema_file)
        assert "fields" in schema
        assert schema["fields"]["name"]["type"] == "string"
    
    def test_load_schema_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_schema("/nonexistent/schema.yaml")


class TestValidateFieldType:
    def test_string_valid(self):
        assert validate_field_type("hello", "string") is True
        assert validate_field_type("hello", "String") is True
    
    def test_string_invalid(self):
        assert validate_field_type(123, "string") is False
    
    def test_int_valid(self):
        assert validate_field_type(42, "int") is True
        assert validate_field_type(0, "int") is True
    
    def test_int_invalid_bool(self):
        # Booleans are technically ints in Python, but we exclude them
        assert validate_field_type(True, "int") is False
    
    def test_float_valid(self):
        assert validate_field_type(3.14, "float") is True
        assert validate_field_type(10, "float") is True # int is valid for float
    
    def test_boolean_valid(self):
        assert validate_field_type(True, "boolean") is True
        assert validate_field_type(False, "boolean") is True
    
    def test_null_valid(self):
        assert validate_field_type(None, "null") is True
        assert validate_field_type(None, "any") is True
    
    def test_date_valid(self):
        assert validate_field_type("2023-01-01", "date") is True
        assert validate_field_type(pd.Timestamp("2023-01-01"), "date") is True
        assert validate_field_type("invalid-date", "date") is False


class TestValidateRecord:
    def test_valid_record(self):
        schema = {
            "fields": {
                "name": {"type": "string"},
                "age": {"type": "int"}
            },
            "required": ["name"]
        }
        record = {"name": "Alice", "age": 30}
        
        errors = validate_record(record, schema)
        assert errors == []
    
    def test_missing_required(self):
        schema = {
            "fields": {"name": {"type": "string"}},
            "required": ["name"]
        }
        record = {}
        
        errors = validate_record(record, schema)
        assert len(errors) == 1
        assert "Missing required field" in errors[0]
    
    def test_type_mismatch(self):
        schema = {
            "fields": {"age": {"type": "int"}},
            "required": []
        }
        record = {"age": "thirty"}
        
        errors = validate_record(record, schema)
        assert len(errors) == 1
        assert "Type mismatch" in errors[0]


class TestValidateParquetSchema:
    @pytest.fixture
    def sample_parquet(self, tmp_path):
        data = {
            "user_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "score": [1.5, 2.5, 3.5]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "test.parquet"
        df.to_parquet(file_path)
        return file_path
    
    def test_valid_parquet(self, sample_parquet, tmp_path):
        schema = {
            "fields": {
                "user_id": {"type": "int"},
                "name": {"type": "string"},
                "score": {"type": "float"}
            },
            "required": ["user_id"]
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        is_valid, errors = validate_parquet_schema(sample_parquet, schema)
        assert is_valid is True
        assert errors == []
    
    def test_missing_column(self, sample_parquet, tmp_path):
        schema = {
            "fields": {"missing_col": {"type": "string"}},
            "required": ["missing_col"]
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        is_valid, errors = validate_parquet_schema(sample_parquet, schema)
        assert is_valid is False
        assert len(errors) > 0


class TestValidateCsvSchema:
    @pytest.fixture
    def sample_csv(self, tmp_path):
        data = "name,age\nAlice,30\nBob,25"
        file_path = tmp_path / "test.csv"
        file_path.write_text(data)
        return file_path
    
    def test_valid_csv(self, sample_csv, tmp_path):
        schema = {
            "fields": {
                "name": {"type": "string"},
                "age": {"type": "int"}
            },
            "required": ["name"]
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        is_valid, errors = validate_csv_schema(sample_csv, schema)
        assert is_valid is True
        assert errors == []
    
    def test_missing_column(self, sample_csv, tmp_path):
        schema = {
            "fields": {"missing": {"type": "string"}},
            "required": ["missing"]
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        is_valid, errors = validate_csv_schema(sample_csv, schema)
        assert is_valid is False


class TestRecordChecksum:
    def test_record_checksum_creates_file(self, tmp_path):
        data_file = tmp_path / "data.txt"
        data_file.write_text("Test content")
        output_file = tmp_path / "checksum.json"
        
        result = record_checksum(data_file, output_file)
        
        assert "checksum" in result
        assert "file_size_bytes" in result
        assert output_file.exists()
        
        with open(output_file) as f:
            saved = json.load(f)
        assert saved["checksum"] == result["checksum"]


class TestValidateAndChecksum:
    def test_full_validation_flow(self, tmp_path):
        # Create CSV
        data = "name,age\nAlice,30"
        data_file = tmp_path / "data.csv"
        data_file.write_text(data)
        
        # Create Schema
        schema = {
            "fields": {"name": {"type": "string"}, "age": {"type": "int"}},
            "required": ["name"]
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        # Checksum path
        checksum_file = tmp_path / "checksum.json"
        
        result = validate_and_checksum(data_file, schema_file, checksum_file)
        
        assert result["is_valid"] is True
        assert checksum_file.exists()
    
    def test_validation_failure_raises(self, tmp_path):
        data = "name,age\nAlice,not_a_number"
        data_file = tmp_path / "data.csv"
        data_file.write_text(data)
        
        schema = {
            "fields": {"name": {"type": "string"}, "age": {"type": "int"}},
            "required": []
        }
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(schema, f)
        
        with pytest.raises(ValidationError):
            validate_and_checksum(data_file, schema_file)