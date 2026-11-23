import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_source import (
    check_url_reachability,
    load_file_content,
    validate_schema,
    save_validation_report,
    validate_source,
    DataFetchError,
    REQUIRED_COLUMNS
)

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with valid data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("year,effect_size,sample_size,field,extra_col\n")
        f.write("2020,0.5,100,psychology,extra\n")
        f.write("2021,0.3,150,biology,extra\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_invalid_csv_file():
    """Create a temporary CSV file with missing columns."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("year,effect_size\n")
        f.write("2020,0.5\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_empty_csv_file():
    """Create a temporary empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("year,effect_size,sample_size,field\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_validate_schema_valid(temp_csv_file):
    """Test schema validation with valid data."""
    rows = load_file_content(temp_csv_file)
    report = validate_schema(rows, REQUIRED_COLUMNS)
    
    assert report["status"] == "valid"
    assert set(report["required_columns"]) == REQUIRED_COLUMNS
    assert not report["missing_columns"]
    assert report["row_count"] == 2

def test_validate_schema_missing_columns(temp_invalid_csv_file):
    """Test schema validation with missing columns."""
    rows = load_file_content(temp_invalid_csv_file)
    report = validate_schema(rows, REQUIRED_COLUMNS)
    
    assert report["status"] == "invalid"
    assert "sample_size" in report["missing_columns"]
    assert "field" in report["missing_columns"]

def test_validate_schema_empty_file(temp_empty_csv_file):
    """Test schema validation with empty data rows."""
    rows = load_file_content(temp_empty_csv_file)
    report = validate_schema(rows, REQUIRED_COLUMNS)
    
    assert report["status"] == "failed"
    assert report["reason"] == "No data rows found in file"

def test_load_file_content_not_found():
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_file_content("non_existent_file.csv")

def test_save_validation_report():
    """Test saving a validation report to JSON."""
    report = {
        "status": "valid",
        "test_key": "test_value"
    }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        temp_path = f.name
    
    try:
        save_validation_report(report, temp_path)
        assert os.path.exists(temp_path)
        
        with open(temp_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report
    finally:
        os.unlink(temp_path)

def test_validate_source_full_flow(temp_csv_file, tmp_path):
    """Test the full validation flow."""
    output_path = str(tmp_path / "validation.json")
    
    # Temporarily modify the input path for the test
    with patch('validate_source.validate_source') as mock_func:
        mock_func.return_value = {"status": "valid"}
        
        result = validate_source(temp_csv_file, output_path)
        
        assert result["status"] == "valid"
        assert os.path.exists(output_path)

def test_validate_source_missing_file(tmp_path):
    """Test validation when input file is missing."""
    input_path = str(tmp_path / "missing.csv")
    output_path = str(tmp_path / "validation.json")
    
    with pytest.raises(DataFetchError):
        validate_source(input_path, output_path)
    
    # Check that the report was still saved
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        report = json.load(f)
    assert report["status"] == "failed"
    assert report["reason"] == "File not found"