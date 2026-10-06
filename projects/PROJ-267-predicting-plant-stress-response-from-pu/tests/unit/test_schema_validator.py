import os
import sys
import csv
import tempfile
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import (
    ValidationResult,
    ValidationStatus,
    validate_csv_schema,
    validate_parquet_schema,
    validate_directory_schema,
    RAW_DATA_SCHEMA,
    PROCESSED_DATA_SCHEMA
)

@pytest.fixture
def valid_csv_file(tmp_path):
    """Create a valid CSV file for testing."""
    file_path = tmp_path / "valid_data.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Accession", "Sample_ID", "Stress_Condition", "Species", "Abundance"])
        writer.writeheader()
        writer.writerow({
            "Accession": "P12345",
            "Sample_ID": "S001",
            "Stress_Condition": "Drought",
            "Species": "Arabidopsis",
            "Abundance": "100.5"
        })
        writer.writerow({
            "Accession": "P12346",
            "Sample_ID": "S002",
            "Stress_Condition": "Salinity",
            "Species": "Rice",
            "Abundance": "200.0"
        })
    return str(file_path)

@pytest.fixture
def invalid_csv_file(tmp_path):
    """Create an invalid CSV file (missing required column)."""
    file_path = tmp_path / "invalid_data.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Accession", "Sample_ID", "Species"])  # Missing Stress_Condition
        writer.writeheader()
        writer.writerow({
            "Accession": "P12345",
            "Sample_ID": "S001",
            "Species": "Arabidopsis"
        })
    return str(file_path)

@pytest.fixture
def type_mismatch_csv_file(tmp_path):
    """Create a CSV file with type mismatch."""
    file_path = tmp_path / "type_mismatch.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Accession", "Sample_ID", "Stress_Condition", "Species", "Abundance"])
        writer.writeheader()
        writer.writerow({
            "Accession": "P12345",
            "Sample_ID": "S001",
            "Stress_Condition": "Drought",
            "Species": "Arabidopsis",
            "Abundance": "not_a_number"  # Should be numeric
        })
    return str(file_path)

def test_validate_csv_schema_valid(valid_csv_file):
    """Test validation of a valid CSV file."""
    result = validate_csv_schema(valid_csv_file, RAW_DATA_SCHEMA)
    assert result.status == ValidationStatus.PASSED
    assert len(result.errors) == 0
    assert result.total_rows == 2
    assert result.valid_rows == 2

def test_validate_csv_schema_missing_columns(invalid_csv_file):
    """Test validation fails when required columns are missing."""
    result = validate_csv_schema(invalid_csv_file, RAW_DATA_SCHEMA)
    assert result.status == ValidationStatus.FAILED
    assert len(result.errors) > 0
    assert any("Missing required columns" in err for err in result.errors)

def test_validate_csv_schema_type_mismatch(type_mismatch_csv_file):
    """Test validation fails when data types are incorrect."""
    result = validate_csv_schema(type_mismatch_csv_file, RAW_DATA_SCHEMA)
    assert result.status == ValidationStatus.FAILED
    assert len(result.errors) > 0
    assert any("Expected" in err and "got" in err for err in result.errors)

def test_validate_csv_schema_file_not_found():
    """Test validation fails when file does not exist."""
    result = validate_csv_schema("non_existent_file.csv", RAW_DATA_SCHEMA)
    assert result.status == ValidationStatus.FAILED
    assert len(result.errors) == 1
    assert "File not found" in result.errors[0]

def test_validate_parquet_schema_valid(tmp_path):
    """Test validation of a valid Parquet file."""
    try:
        import pandas as pd
        file_path = tmp_path / "valid_data.parquet"
        df = pd.DataFrame({
            "Sample_ID": ["S001", "S002"],
            "Stress_Condition": ["Drought", "Salinity"],
            "Species": ["Arabidopsis", "Rice"],
            "Protein_ID": ["P12345", "P12346"],
            "Normalized_Abundance": [100.5, 200.0]
        })
        df.to_parquet(file_path)
        
        result = validate_parquet_schema(str(file_path), PROCESSED_DATA_SCHEMA)
        assert result.status == ValidationStatus.PASSED
        assert result.total_rows == 2
        assert result.valid_rows == 2
    except ImportError:
        pytest.skip("pandas not installed")

def test_validate_parquet_schema_missing_columns(tmp_path):
    """Test validation fails for Parquet file with missing columns."""
    try:
        import pandas as pd
        file_path = tmp_path / "invalid_data.parquet"
        df = pd.DataFrame({
            "Sample_ID": ["S001"],
            "Species": ["Arabidopsis"]
            # Missing required columns
        })
        df.to_parquet(file_path)
        
        result = validate_parquet_schema(str(file_path), PROCESSED_DATA_SCHEMA)
        assert result.status == ValidationStatus.FAILED
        assert len(result.errors) > 0
    except ImportError:
        pytest.skip("pandas not installed")

def test_validate_directory_schema(tmp_path):
    """Test validation of all files in a directory."""
    # Create valid and invalid files
    valid_file = tmp_path / "valid.csv"
    with open(valid_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Accession", "Sample_ID", "Stress_Condition", "Species", "Abundance"])
        writer.writeheader()
        writer.writerow({
            "Accession": "P12345",
            "Sample_ID": "S001",
            "Stress_Condition": "Drought",
            "Species": "Arabidopsis",
            "Abundance": "100.5"
        })
    
    invalid_file = tmp_path / "invalid.csv"
    with open(invalid_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Accession", "Sample_ID"])
        writer.writeheader()
        writer.writerow({"Accession": "P12345", "Sample_ID": "S001"})
    
    schema_map = {".csv": RAW_DATA_SCHEMA}
    results = validate_directory_schema(str(tmp_path), schema_map)
    
    assert len(results) == 2
    assert results[str(valid_file)].status == ValidationStatus.PASSED
    assert results[str(invalid_file)].status == ValidationStatus.FAILED

def test_validation_result_dataclass():
    """Test the ValidationResult dataclass initialization."""
    result = ValidationResult(
        status=ValidationStatus.WARNING,
        file_path="test.csv",
        errors=["Error 1"],
        warnings=["Warning 1"],
        valid_rows=10,
        total_rows=10
    )
    
    assert result.status == ValidationStatus.WARNING
    assert result.file_path == "test.csv"
    assert result.errors == ["Error 1"]
    assert result.warnings == ["Warning 1"]
    assert result.valid_rows == 10
    assert result.total_rows == 10
