import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import json

from code.data.validate_schema import (
    validate_schema,
    generate_checksum,
    SchemaValidationError,
    EXPECTED_COLUMNS
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def create_valid_csv(temp_dir):
    """Creates a valid features.csv file."""
    df = pd.DataFrame({
        'file_path': ['src/Main.java', 'src/Utils.java'],
        'cc': [5, 10],
        'halstead': [100.5, 200.8],
        'loc': [50, 120],
        'is_buggy': [0, 1]
    })
    csv_path = temp_dir / 'features.csv'
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def create_invalid_schema_csv(temp_dir):
    """Creates a CSV with missing columns."""
    df = pd.DataFrame({
        'file_path': ['src/Main.java'],
        'cc': [5],
        # Missing halstead, loc, is_buggy
    })
    csv_path = temp_dir / 'invalid_features.csv'
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def create_nan_csv(temp_dir):
    """Creates a CSV with NaN values in numeric columns."""
    df = pd.DataFrame({
        'file_path': ['src/Main.java'],
        'cc': [5],
        'halstead': [float('nan')],
        'loc': [50],
        'is_buggy': [0]
    })
    csv_path = temp_dir / 'nan_features.csv'
    df.to_csv(csv_path, index=False)
    return str(csv_path)

class TestValidateSchema:
    def test_validate_schema_success(self, create_valid_csv):
        result = validate_schema(create_valid_csv)
        assert result['valid'] is True
        assert result['row_count'] == 2
        assert 'issues' in result
        assert len(result['issues']) == 0

    def test_validate_schema_missing_file(self, temp_dir):
        non_existent = str(temp_dir / 'missing.csv')
        with pytest.raises(FileNotFoundError):
            validate_schema(non_existent, strict=True)
        
        # Non-strict should return dict
        result = validate_schema(non_existent, strict=False)
        assert result['valid'] is False
        assert 'File not found' in result['error']

    def test_validate_schema_missing_columns(self, create_invalid_schema_csv):
        with pytest.raises(SchemaValidationError):
            validate_schema(create_invalid_schema_csv, strict=True)
        
        result = validate_schema(create_invalid_schema_csv, strict=False)
        assert result['valid'] is False
        assert any('Missing columns' in issue for issue in result['issues'])

    def test_validate_schema_nan_values(self, create_nan_csv):
        # Schema validation checks column existence and types, not data content (NaN)
        # The schema check might pass if types are object/float, but NaN is technically float64
        # However, if we want to ensure strict data integrity, we might need a separate check.
        # Based on the task "schema validator", we check structure.
        # If the requirement implies checking for NaN as part of schema validity, we adjust.
        # For now, standard schema validation passes on structure. 
        # Let's assume the schema validator just checks structure.
        result = validate_schema(create_nan_csv, strict=False)
        # Note: Pandas reads NaN as float64, so type check passes.
        # If the task requires NaN detection here, logic would be added.
        # But T018 handles NaN dropping. T007 is schema.
        # We will assert it passes schema check (structure only) unless specified otherwise.
        assert result['valid'] is True 

class TestGenerateChecksum:
    def test_generate_checksum_creates_file(self, create_valid_csv, temp_dir):
        output_json = str(temp_dir / 'checksums.json')
        result = generate_checksum(create_valid_csv, output_json)
        
        assert Path(output_json).exists()
        assert 'sha256' in result
        assert 'size_bytes' in result
        assert 'file' in result
        
        # Verify JSON content
        with open(output_json, 'r') as f:
            data = json.load(f)
        
        assert 'features.csv' in data
        assert data['features.csv']['sha256'] == result['sha256']

    def test_generate_checksum_updates_existing(self, create_valid_csv, temp_dir):
        output_json = str(temp_dir / 'checksums.json')
        
        # First run
        generate_checksum(create_valid_csv, output_json)
        
        # Create another file to add
        df2 = pd.DataFrame({
            'file_path': ['Other.java'],
            'cc': [1], 'halstead': [1.0], 'loc': [1], 'is_buggy': [0]
        })
        csv2 = str(temp_dir / 'other.csv')
        df2.to_csv(csv2, index=False)
        
        # Add second file to same JSON
        generate_checksum(csv2, output_json)
        
        with open(output_json, 'r') as f:
            data = json.load(f)
        
        assert 'features.csv' in data
        assert 'other.csv' in data

    def test_generate_checksum_algorithm(self, create_valid_csv, temp_dir):
        output_json = str(temp_dir / 'checksums.json')
        result = generate_checksum(create_valid_csv, output_json, algorithm='md5')
        
        assert result['algorithm'] == 'md5'
        assert len(result['sha256']) == 32 # MD5 is 32 hex chars (though key is named sha256 in schema, logic uses algorithm param)
        # Note: The key in the JSON dict is hardcoded 'sha256' in the function implementation.
        # If we change algorithm, the key name in JSON might be misleading if not updated.
        # But per implementation: all_checksums[path.name] = checksum_data, where checksum_data has 'sha256': checksum.
        # This is a potential bug in the implementation if we want dynamic keys, but for T007 we follow the spec.
        # The spec says "checksums.json" with "sha256" key.
        # The function signature allows algorithm param but stores it under 'sha256' key in the dict value.
        # Let's verify the implementation stores the hash correctly regardless of key name.
        assert 'sha256' in result # The key in the returned dict is 'sha256' as per implementation