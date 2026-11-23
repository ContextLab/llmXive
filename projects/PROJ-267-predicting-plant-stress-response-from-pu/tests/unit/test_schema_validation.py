import os
import sys
import tempfile
import json
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.schema_validator import (
    ValidationResult,
    ValidationStatus,
    validate_csv_schema,
    validate_parquet_schema,
    validate_directory_schema,
    RAW_SCHEMA_REQUIRED_COLUMNS,
    PROCESSED_SCHEMA_REQUIRED_COLUMNS
)

@pytest.fixture
def temp_csv_raw():
    """Create a temporary CSV file with raw data schema"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sample_id,species,stress_condition,protein_A\n")
        f.write("S001,Arabidopsis,drought,10.5\n")
        f.write("S002,Rice,salinity,20.3\n")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_csv_processed():
    """Create a temporary CSV file with processed data schema"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sample_id,species,stress_condition,protein_A,protein_B\n")
        f.write("S001,Arabidopsis,drought,10.5,15.2\n")
        f.write("S002,Rice,salinity,20.3,18.7\n")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_csv_invalid():
    """Create a temporary CSV file with missing required columns"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sample_id,species\n")  # Missing stress_condition
        f.write("S001,Arabidopsis\n")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_validate_csv_schema_raw_valid(temp_csv_raw):
    """Test validation of a valid raw CSV file"""
    result = validate_csv_schema(temp_csv_raw, 'raw')
    assert result.status == ValidationStatus.VALID
    assert 'Missing required columns' not in result.message
    assert result.file_path == str(temp_csv_raw)

def test_validate_csv_schema_processed_valid(temp_csv_processed):
    """Test validation of a valid processed CSV file"""
    result = validate_csv_schema(temp_csv_processed, 'processed')
    assert result.status == ValidationStatus.VALID
    assert 'Missing required columns' not in result.message

def test_validate_csv_schema_invalid_columns(temp_csv_invalid):
    """Test validation of a CSV file with missing required columns"""
    result = validate_csv_schema(temp_csv_invalid, 'raw')
    assert result.status == ValidationStatus.INVALID
    assert 'Missing required columns' in result.message
    assert 'stress_condition' in result.message

def test_validate_csv_schema_file_not_found():
    """Test validation of a non-existent file"""
    result = validate_csv_schema(Path('/nonexistent/file.csv'), 'raw')
    assert result.status == ValidationStatus.INVALID
    assert 'File not found' in result.message

def test_validate_csv_schema_empty_file(temp_dir):
    """Test validation of an empty CSV file"""
    empty_file = temp_dir / 'empty.csv'
    empty_file.touch()
    
    result = validate_csv_schema(empty_file, 'raw')
    assert result.status == ValidationStatus.INVALID
    assert 'empty' in result.message.lower() or 'no headers' in result.message.lower()

def test_validate_csv_schema_invalid_prefix(temp_dir):
    """Test validation of a processed CSV with invalid column prefixes"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("sample_id,species,stress_condition,invalid_col\n")
        f.write("S001,Arabidopsis,drought,10.5\n")
        temp_path = Path(f.name)
    
    try:
        result = validate_csv_schema(temp_path, 'processed')
        assert result.status == ValidationStatus.WARNING
        assert 'invalid_col' in result.message
    finally:
        os.unlink(temp_path)

def test_validate_directory_schema(temp_dir):
    """Test validation of all files in a directory"""
    # Create valid and invalid files
    valid_file = temp_dir / 'valid.csv'
    valid_file.write_text("sample_id,species,stress_condition\nS001,Arabidopsis,drought\n")
    
    invalid_file = temp_dir / 'invalid.csv'
    invalid_file.write_text("sample_id,species\nS001,Arabidopsis\n")  # Missing stress_condition
    
    results = validate_directory_schema(temp_dir)
    
    assert len(results) == 2
    valid_results = [r for r in results if r.status == ValidationStatus.VALID]
    invalid_results = [r for r in results if r.status == ValidationStatus.INVALID]
    
    assert len(valid_results) == 1
    assert len(invalid_results) == 1

def test_validate_directory_schema_nonexistent():
    """Test validation of a non-existent directory"""
    results = validate_directory_schema(Path('/nonexistent/dir'))
    assert results == []

def test_result_dataclass():
    """Test ValidationResult dataclass"""
    result = ValidationResult(
        status=ValidationStatus.VALID,
        message="Test message",
        file_path="test.csv",
        details={'key': 'value'}
    )
    
    assert result.status == ValidationStatus.VALID
    assert result.message == "Test message"
    assert result.file_path == "test.csv"
    assert result.details == {'key': 'value'}
    
    # Test default empty details
    result2 = ValidationResult(
        status=ValidationStatus.INVALID,
        message="Another message"
    )
    assert result2.details == {}