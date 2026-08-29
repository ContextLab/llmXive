import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import json
from data.validate_schema import validate_schema, generate_checksum

def create_valid_csv(tmp_path):
    """Helper to create a valid features.csv"""
    df = pd.DataFrame({
        'file_path': ['src/A.java', 'src/B.java'],
        'cc': [5, 10],
        'halstead': [100.5, 200.5],
        'loc': [50, 100],
        'is_buggy': [1, 0]
    })
    csv_path = tmp_path / "features.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def create_invalid_schema_csv(tmp_path):
    """Helper to create a CSV with missing columns"""
    df = pd.DataFrame({
        'file_path': ['src/A.java'],
        'cc': [5],
        # Missing halstead, loc, is_buggy
    })
    csv_path = tmp_path / "features_invalid.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def create_nan_csv(tmp_path):
    """Helper to create a CSV with NaN values"""
    df = pd.DataFrame({
        'file_path': ['src/A.java', 'src/B.java'],
        'cc': [5, None],
        'halstead': [100.5, 200.5],
        'loc': [50, 100],
        'is_buggy': [1, 0]
    })
    csv_path = tmp_path / "features_nan.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

class TestValidateSchema:
    def test_valid_schema_passes(self, tmp_path):
        csv_path = create_valid_csv(tmp_path)
        is_valid, errors = validate_schema(str(csv_path))
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_columns_fails(self, tmp_path):
        csv_path = create_invalid_schema_csv(tmp_path)
        is_valid, errors = validate_schema(str(csv_path))
        assert is_valid is False
        assert any("Missing required columns" in err for err in errors)

    def test_nan_values_fail(self, tmp_path):
        csv_path = create_nan_csv(tmp_path)
        is_valid, errors = validate_schema(str(csv_path))
        assert is_valid is False
        assert any("NaN" in err for err in errors)

    def test_file_not_found(self, tmp_path):
        is_valid, errors = validate_schema(str(tmp_path / "nonexistent.csv"))
        assert is_valid is False
        assert any("not found" in err for err in errors)

class TestGenerateChecksum:
    def test_checksum_generation(self, tmp_path):
        csv_path = create_valid_csv(tmp_path)
        checksum_path = tmp_path / "checksums.json"
        
        result = generate_checksum(str(csv_path), str(checksum_path))
        
        assert result['file'] == "features.csv"
        assert result['algorithm'] == "sha256"
        assert 'sha256' in result
        assert 'size_bytes' in result
        assert 'timestamp' in result
        
        # Verify file was written
        assert checksum_path.exists()
        
        # Verify content matches
        with open(checksum_path, 'r') as f:
            loaded = json.load(f)
        assert loaded['sha256'] == result['sha256']

    def test_file_not_found_raises(self, tmp_path):
        checksum_path = tmp_path / "checksums.json"
        with pytest.raises(FileNotFoundError):
            generate_checksum(str(tmp_path / "nonexistent.csv"), str(checksum_path))