import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import yaml

from code.analysis.verify_schemas import (
    load_schema,
    compute_file_hash,
    validate_csv_schema,
    validate_json_schema,
    run_schema_validation
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_csv_schema():
    """Sample CSV schema for testing."""
    return {
        'columns': {
            'thread_id': {
                'type': 'string',
                'required': True,
                'allow_null': False
            },
            'sentiment_score': {
                'type': 'float',
                'required': True,
                'allow_null': True,
                'min': -1.0,
                'max': 1.0
            },
            'reply_count': {
                'type': 'int',
                'required': True,
                'allow_null': False,
                'min': 0
            }
        }
    }

@pytest.fixture
def sample_json_schema():
    """Sample JSON schema for testing."""
    return {
        'required': ['status', 'files_checked'],
        'properties': {
            'status': {
                'type': 'string',
                'enum': ['pass', 'fail']
            },
            'files_checked': {
                'type': 'integer',
                'minimum': 0
            },
            'errors': {
                'type': 'array'
            }
        }
    }

def test_load_schema_valid(temp_dir, sample_csv_schema):
    """Test loading a valid schema file."""
    schema_file = temp_dir / 'test_schema.yaml'
    with open(schema_file, 'w') as f:
        yaml.dump(sample_csv_schema, f)
    
    loaded_schema = load_schema(schema_file)
    assert loaded_schema == sample_csv_schema

def test_load_schema_missing_file(temp_dir):
    """Test loading a non-existent schema file raises error."""
    schema_file = temp_dir / 'nonexistent.yaml'
    with pytest.raises(FileNotFoundError):
        load_schema(schema_file)

def test_compute_file_hash(temp_dir):
    """Test file hash computation."""
    test_file = temp_dir / 'test.txt'
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    hash1 = compute_file_hash(test_file)
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters
    
    # Change content and verify hash changes
    test_file.write_text("Different content")
    hash2 = compute_file_hash(test_file)
    assert hash1 != hash2

def test_validate_csv_schema_valid(sample_csv_schema):
    """Test CSV validation with valid data."""
    df = pd.DataFrame({
        'thread_id': ['1', '2', '3'],
        'sentiment_score': [0.5, -0.3, 0.0],
        'reply_count': [10, 5, 20]
    })
    
    errors = validate_csv_schema(df, sample_csv_schema)
    assert len(errors) == 0

def test_validate_csv_schema_missing_column(sample_csv_schema):
    """Test CSV validation with missing required column."""
    df = pd.DataFrame({
        'thread_id': ['1', '2', '3'],
        'sentiment_score': [0.5, -0.3, 0.0]
        # Missing reply_count
    })
    
    errors = validate_csv_schema(df, sample_csv_schema)
    assert any('Missing required columns' in error for error in errors)

def test_validate_csv_schema_null_value(sample_csv_schema):
    """Test CSV validation with null value where not allowed."""
    df = pd.DataFrame({
        'thread_id': ['1', None, '3'],
        'sentiment_score': [0.5, -0.3, 0.0],
        'reply_count': [10, 5, 20]
    })
    
    errors = validate_csv_schema(df, sample_csv_schema)
    assert any('contains null values' in error for error in errors)

def test_validate_csv_schema_out_of_range(sample_csv_schema):
    """Test CSV validation with value out of range."""
    df = pd.DataFrame({
        'thread_id': ['1', '2', '3'],
        'sentiment_score': [0.5, 1.5, 0.0],  # 1.5 is > max 1.0
        'reply_count': [10, 5, 20]
    })
    
    errors = validate_csv_schema(df, sample_csv_schema)
    assert any('above maximum' in error for error in errors)

def test_validate_json_schema_valid(sample_json_schema):
    """Test JSON validation with valid data."""
    data = {
        'status': 'pass',
        'files_checked': 10,
        'errors': []
    }
    
    errors = validate_json_schema(data, sample_json_schema)
    assert len(errors) == 0

def test_validate_json_schema_missing_required(sample_json_schema):
    """Test JSON validation with missing required field."""
    data = {
        'files_checked': 10
        # Missing status
    }
    
    errors = validate_json_schema(data, sample_json_schema)
    assert any('Missing required fields' in error for error in errors)

def test_validate_json_schema_invalid_enum(sample_json_schema):
    """Test JSON validation with invalid enum value."""
    data = {
        'status': 'invalid_status',
        'files_checked': 10
    }
    
    errors = validate_json_schema(data, sample_json_schema)
    assert any('not in allowed values' in error for error in errors)

def test_validate_json_schema_out_of_range(sample_json_schema):
    """Test JSON validation with value out of range."""
    data = {
        'status': 'pass',
        'files_checked': -5  # Below minimum 0
    }
    
    errors = validate_json_schema(data, sample_json_schema)
    assert any('below minimum' in error for error in errors)

def test_run_schema_validation(temp_dir, sample_csv_schema, sample_json_schema):
    """Test end-to-end schema validation."""
    # Create contracts directory with schema
    contracts_dir = temp_dir / 'contracts'
    contracts_dir.mkdir()
    
    csv_schema_file = contracts_dir / 'threads.yaml'
    with open(csv_schema_file, 'w') as f:
        yaml.dump(sample_csv_schema, f)
    
    json_schema_file = contracts_dir / 'report.yaml'
    with open(json_schema_file, 'w') as f:
        yaml.dump(sample_json_schema, f)
    
    # Create processed directory with valid files
    processed_dir = temp_dir / 'processed'
    processed_dir.mkdir()
    
    # Valid CSV
    df = pd.DataFrame({
        'thread_id': ['1', '2', '3'],
        'sentiment_score': [0.5, -0.3, 0.0],
        'reply_count': [10, 5, 20]
    })
    df.to_csv(processed_dir / 'threads.csv', index=False)
    
    # Valid JSON
    data = {
        'status': 'pass',
        'files_checked': 10,
        'errors': []
    }
    with open(processed_dir / 'report.json', 'w') as f:
        json.dump(data, f)
    
    # Run validation
    output_path = temp_dir / 'validation_report.json'
    report = run_schema_validation(processed_dir, contracts_dir, output_path)
    
    # Verify results
    assert report['status'] == 'pass'
    assert report['files_checked'] == 2
    assert report['files_passed'] == 2
    assert report['files_failed'] == 0
    assert len(report['errors']) == 0
    
    # Verify report file was created
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    assert saved_report == report

def test_run_schema_validation_with_errors(temp_dir, sample_csv_schema):
    """Test schema validation with invalid files."""
    # Create contracts directory with schema
    contracts_dir = temp_dir / 'contracts'
    contracts_dir.mkdir()
    
    csv_schema_file = contracts_dir / 'threads.yaml'
    with open(csv_schema_file, 'w') as f:
        yaml.dump(sample_csv_schema, f)
    
    # Create processed directory with invalid file
    processed_dir = temp_dir / 'processed'
    processed_dir.mkdir()
    
    # Invalid CSV (missing required column)
    df = pd.DataFrame({
        'thread_id': ['1', '2', '3'],
        'sentiment_score': [0.5, -0.3, 0.0]
        # Missing reply_count
    })
    df.to_csv(processed_dir / 'threads.csv', index=False)
    
    # Run validation
    output_path = temp_dir / 'validation_report.json'
    report = run_schema_validation(processed_dir, contracts_dir, output_path)
    
    # Verify results
    assert report['status'] == 'fail'
    assert report['files_checked'] == 1
    assert report['files_passed'] == 0
    assert report['files_failed'] == 1
    assert len(report['errors']) > 0
    assert any('Missing required columns' in error for error in report['errors'])

def test_run_schema_validation_missing_processed_dir(temp_dir):
    """Test schema validation when processed directory doesn't exist."""
    contracts_dir = temp_dir / 'contracts'
    contracts_dir.mkdir()
    
    output_path = temp_dir / 'validation_report.json'
    report = run_schema_validation(
        temp_dir / 'nonexistent', 
        contracts_dir, 
        output_path
    )
    
    assert report['status'] == 'fail'
    assert 'Processed directory does not exist' in report['errors'][0]

def test_run_schema_validation_missing_contracts_dir(temp_dir):
    """Test schema validation when contracts directory doesn't exist."""
    processed_dir = temp_dir / 'processed'
    processed_dir.mkdir()
    
    output_path = temp_dir / 'validation_report.json'
    report = run_schema_validation(
        processed_dir,
        temp_dir / 'nonexistent',
        output_path
    )
    
    assert report['status'] == 'fail'
    assert 'Contracts directory does not exist' in report['errors'][0]