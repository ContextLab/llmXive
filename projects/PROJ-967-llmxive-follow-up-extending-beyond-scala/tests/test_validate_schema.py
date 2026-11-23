import pytest
from pathlib import Path
import tempfile
import csv
import yaml

from code.validate_schema import (
    load_schema,
    get_expected_columns,
    validate_dataset,
    setup_logging
)

@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "version": "1.0",
        "required_fields": ["prompt", "image_path", "teacher_logits", "student_scalar"],
        "column_types": {
            "prompt": "string",
            "image_path": "string",
            "teacher_logits": "list[float]",
            "student_scalar": "float"
        }
    }
    return schema

@pytest.fixture
def schema_file(sample_schema):
    """Create a temporary schema YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(sample_schema, f)
        return Path(f.name)

@pytest.fixture
def valid_dataset_file():
    """Create a temporary CSV file with valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["prompt", "image_path", "teacher_logits", "student_scalar"])
        writer.writerow(["Test prompt", "/path/to/image.jpg", "[0.5, 0.5, 0.5, 0.5]", "0.5"])
        return Path(f.name)

@pytest.fixture
def invalid_dataset_file():
    """Create a temporary CSV file with missing columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["prompt", "image_path"])  # Missing required columns
        writer.writerow(["Test prompt", "/path/to/image.jpg"])
        return Path(f.name)

def test_load_schema_valid(schema_file):
    """Test loading a valid schema file."""
    schema = load_schema(schema_file)
    assert "version" in schema
    assert "required_fields" in schema
    assert schema["version"] == "1.0"

def test_load_schema_missing_file():
    """Test loading a non-existent schema file raises error."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path("non_existent_file.yaml"))

def test_get_expected_columns(sample_schema):
    """Test extracting expected columns from schema."""
    columns = get_expected_columns(sample_schema)
    assert len(columns) == 4
    assert "prompt" in columns
    assert "student_scalar" in columns

def test_validate_dataset_valid(schema_file, valid_dataset_file):
    """Test validation of a valid dataset."""
    logger = setup_logging()
    expected_columns = get_expected_columns(load_schema(schema_file))
    
    result = validate_dataset(valid_dataset_file, expected_columns, logger)
    assert result is True

def test_validate_dataset_invalid(schema_file, invalid_dataset_file):
    """Test validation of a dataset with missing columns."""
    logger = setup_logging()
    expected_columns = get_expected_columns(load_schema(schema_file))
    
    with pytest.raises(ValueError, match="Schema validation FAILED"):
        validate_dataset(invalid_dataset_file, expected_columns, logger)

def test_validate_dataset_missing_file(schema_file):
    """Test validation of a non-existent dataset."""
    logger = setup_logging()
    expected_columns = get_expected_columns(load_schema(schema_file))
    
    with pytest.raises(FileNotFoundError):
        validate_dataset(Path("non_existent.csv"), expected_columns, logger)
