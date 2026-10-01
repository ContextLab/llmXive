import os
import sys
import tempfile
import pytest
from pathlib import Path
import csv
import json

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import (
    ValidationResult,
    ValidationStatus,
    validate_csv_schema,
    validate_parquet_schema,
    validate_directory_schema,
    main
)

class TestValidationResult:
    """Test the ValidationResult dataclass."""
    
    def test_creation_default(self):
        result = ValidationResult(status=ValidationStatus.PASSED)
        assert result.status == ValidationStatus.PASSED
        assert result.errors == []
        assert result.warnings == []
        assert result.files_checked == 0
        assert result.total_rows == 0
    
    def test_creation_with_data(self):
        result = ValidationResult(
            status=ValidationStatus.FAILED,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            files_checked=5,
            total_rows=100
        )
        assert result.status == ValidationStatus.FAILED
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.files_checked == 5
        assert result.total_rows == 100

class TestValidateCSVS:
    """Test CSV schema validation."""
    
    def test_valid_proteomic_csv(self, tmp_path):
        # Create a valid proteomic CSV
        csv_path = tmp_path / "valid_proteomic.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": 10.5})
            writer.writerow({"protein_id": "P12346", "sample_id": "S002", "abundance": 20.3})
        
        result = validate_csv_schema(csv_path, "proteomic")
        assert result.status == ValidationStatus.PASSED
        assert result.errors == []
        assert result.total_rows == 2
    
    def test_missing_required_columns(self, tmp_path):
        # Create CSV missing required columns
        csv_path = tmp_path / "missing_cols.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["abundance", "sample_id"])
            writer.writeheader()
            writer.writerow({"abundance": 10.5, "sample_id": "S001"})
        
        result = validate_csv_schema(csv_path, "proteomic")
        assert result.status == ValidationStatus.FAILED
        assert "Missing required columns" in result.errors[0]
        assert "protein_id" in result.errors[0]
    
    def test_invalid_file_not_found(self):
        result = validate_csv_schema(Path("/nonexistent/file.csv"), "proteomic")
        assert result.status == ValidationStatus.FAILED
        assert "File not found" in result.errors[0]
    
    def test_type_mismatch_warning(self, tmp_path):
        # Create CSV with type mismatch
        csv_path = tmp_path / "type_mismatch.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": "not_a_number"})
        
        result = validate_csv_schema(csv_path, "proteomic")
        assert result.status == ValidationStatus.PASSED  # Type mismatch is a warning, not failure
        assert len(result.warnings) > 0
        assert "Invalid value" in result.warnings[0] or "Type mismatch" in result.warnings[0]
    
    def test_empty_file(self, tmp_path):
        # Create empty CSV file
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        
        result = validate_csv_schema(csv_path, "proteomic")
        assert result.status == ValidationStatus.FAILED
        assert "no headers" in result.errors[0]

class TestValidateParquetSchema:
    """Test Parquet schema validation."""
    
    def test_valid_parquet(self, tmp_path):
        # Skip if pandas not available
        try:
            import pandas as pd
            import pyarrow as pa
        except ImportError:
            pytest.skip("pandas or pyarrow not available")
        
        # Create a valid parquet file
        parquet_path = tmp_path / "valid.parquet"
        df = pd.DataFrame({
            "protein_id": ["P12345", "P12346"],
            "sample_id": ["S001", "S002"],
            "expression_value": [10.5, 20.3]
        })
        df.to_parquet(parquet_path)
        
        result = validate_parquet_schema(parquet_path, "merged")
        assert result.status == ValidationStatus.PASSED
        assert result.total_rows == 2
    
    def test_missing_required_columns_parquet(self, tmp_path):
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")
        
        # Create parquet missing required columns
        parquet_path = tmp_path / "missing.parquet"
        df = pd.DataFrame({
            "abundance": [10.5, 20.3],
            "sample_id": ["S001", "S002"]
        })
        df.to_parquet(parquet_path)
        
        result = validate_parquet_schema(parquet_path, "merged")
        assert result.status == ValidationStatus.FAILED
        assert "Missing required columns" in result.errors[0]

class TestValidateDirectorySchema:
    """Test directory-level schema validation."""
    
    def test_valid_directory(self, tmp_path):
        # Create valid CSV files
        csv1 = tmp_path / "valid1.csv"
        with open(csv1, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": 10.5})
        
        csv2 = tmp_path / "valid2.csv"
        with open(csv2, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12346", "sample_id": "S002", "abundance": 20.3})
        
        result = validate_directory_schema(tmp_path, "proteomic")
        assert result.status == ValidationStatus.PASSED
        assert result.files_checked == 2
        assert result.total_rows == 2
    
    def test_directory_not_found(self):
        result = validate_directory_schema(Path("/nonexistent/directory"), "proteomic")
        assert result.status == ValidationStatus.FAILED
        assert "Directory not found" in result.errors[0]
    
    def test_empty_directory(self, tmp_path):
        result = validate_directory_schema(tmp_path, "proteomic")
        assert result.status == ValidationStatus.PASSED
        assert len(result.warnings) > 0
        assert "No CSV or Parquet files found" in result.warnings[0]
    
    def test_mixed_valid_invalid(self, tmp_path):
        # Create one valid and one invalid file
        valid_csv = tmp_path / "valid.csv"
        with open(valid_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": 10.5})
        
        invalid_csv = tmp_path / "invalid.csv"
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["abundance", "sample_id"])
            writer.writeheader()
            writer.writerow({"abundance": 10.5, "sample_id": "S001"})
        
        result = validate_directory_schema(tmp_path, "proteomic")
        assert result.status == ValidationStatus.FAILED
        assert result.files_checked == 2
        assert len(result.errors) > 0

class TestMainFunction:
    """Test the main CLI function."""
    
    def test_main_with_valid_directory(self, tmp_path, capsys):
        # Create a valid CSV
        csv_path = tmp_path / "valid.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": 10.5})
        
        # Test main with directory argument
        sys.argv = ['schema_validator.py', '--directory', str(tmp_path), '--schema-type', 'proteomic']
        exit_code = main()
        
        assert exit_code == 0
    
    def test_main_with_invalid_directory(self, capsys):
        # Test main with non-existent directory
        sys.argv = ['schema_validator.py', '--directory', '/nonexistent/path']
        exit_code = main()
        
        assert exit_code == 1
    
    def test_main_with_output_file(self, tmp_path):
        # Create a valid CSV
        csv_path = tmp_path / "valid.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["protein_id", "sample_id", "abundance"])
            writer.writeheader()
            writer.writerow({"protein_id": "P12345", "sample_id": "S001", "abundance": 10.5})
        
        output_file = tmp_path / "report.json"
        sys.argv = ['schema_validator.py', '--directory', str(tmp_path), '--output', str(output_file)]
        exit_code = main()
        
        assert exit_code == 0
        assert output_file.exists()
        
        with open(output_file) as f:
            report = json.load(f)
        
        assert report["status"] == "passed"
        assert report["files_checked"] == 1
