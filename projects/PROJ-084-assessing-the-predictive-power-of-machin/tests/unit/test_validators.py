"""
Unit tests for the dataset and output validators.
"""

import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
from pydantic import ValidationError

from utils.validators import (
    DatasetRecord,
    DatasetSchema,
    OutputRecord,
    OutputSchema,
    MetricsRecord,
    load_schema,
    validate_dataset_file,
    validate_output_file,
    save_validation_report
)

# --- Fixtures ---

@pytest.fixture
def sample_schema_path(tmp_path):
    """Create a temporary schema file for testing"""
    schema_content = """
    fields:
      - name: smiles
        type: string
        constraints:
          non_null: true
      - name: yield
        type: float
        constraints:
          min: 0.0
          max: 100.0
      - name: reaction_class
        type: string
      - name: fingerprint_ecfp
        type: list
        constraints:
          length: 2048
      - name: fingerprint_maccs
        type: list
        constraints:
          length: 167
    """
    path = tmp_path / "test_schema.yaml"
    path.write_text(schema_content)
    return path

@pytest.fixture
def valid_dataset_row():
    """Create a valid dataset row"""
    return {
        "smiles": "CCO",
        "yield": 85.5,
        "reaction_class": "substitution",
        "fingerprint_ecfp": [0] * 2048,
        "fingerprint_maccs": [0] * 167
    }

@pytest.fixture
def invalid_yield_row():
    """Create a row with invalid yield"""
    return {
        "smiles": "CCO",
        "yield": 150.0,  # Out of range
        "reaction_class": "substitution",
        "fingerprint_ecfp": [0] * 2048,
        "fingerprint_maccs": [0] * 167
    }

@pytest.fixture
def invalid_fingerprint_row():
    """Create a row with invalid fingerprint length"""
    return {
        "smiles": "CCO",
        "yield": 50.0,
        "reaction_class": "substitution",
        "fingerprint_ecfp": [0] * 100,  # Wrong length
        "fingerprint_maccs": [0] * 167
    }

@pytest.fixture
def valid_output_record():
    """Create a valid output record"""
    return {
        "model_type": "Random Forest",
        "hyperparameters": {"n_estimators": 100, "max_depth": 10},
        "metrics": {"R2": 0.85, "RMSE": 12.3, "MAE": 8.5},
        "split_ratios": {"train": 0.7, "val": 0.15, "test": 0.15}
    }

# --- Tests ---

class TestDatasetRecord:
    def test_valid_record(self, valid_dataset_row):
        record = DatasetRecord(**valid_dataset_row)
        assert record.smiles == "CCO"
        assert record.yield_val == 85.5
        assert record.reaction_class == "substitution"
        assert len(record.fingerprint_ecfp) == 2048
        assert len(record.fingerprint_maccs) == 167
    
    def test_invalid_yield(self, invalid_yield_row):
        with pytest.raises(ValidationError):
            DatasetRecord(**invalid_yield_row)
    
    def test_invalid_fingerprint_length(self, invalid_fingerprint_row):
        with pytest.raises(ValidationError):
            DatasetRecord(**invalid_fingerprint_row)
    
    def test_invalid_reaction_class(self):
        row = {
            "smiles": "CCO",
            "yield": 50.0,
            "reaction_class": "invalid_class",
            "fingerprint_ecfp": [0] * 2048,
            "fingerprint_maccs": [0] * 167
        }
        with pytest.raises(ValidationError):
            DatasetRecord(**row)

class TestOutputRecord:
    def test_valid_output(self, valid_output_record):
        record = OutputRecord(**valid_output_record)
        assert record.model_type == "Random Forest"
        assert record.metrics.R2 == 0.85
        assert record.split_ratios["train"] == 0.7

class TestValidators:
    def test_load_schema(self, sample_schema_path):
        schema = load_schema(sample_schema_path)
        assert "fields" in schema
        assert len(schema["fields"]) == 5
    
    def test_save_validation_report(self, tmp_path):
        report = {"test": "data", "count": 42}
        output_path = tmp_path / "report.json"
        save_validation_report(report, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == report

class TestFileValidation:
    def test_validate_dataset_file(self, tmp_path, sample_schema_path, valid_dataset_row):
        # Create a test parquet file
        df = pd.DataFrame([valid_dataset_row, valid_dataset_row])
        data_path = tmp_path / "test_data.parquet"
        df.to_parquet(data_path)
        
        # This should not raise
        result = validate_dataset_file(data_path, sample_schema_path)
        assert result["valid_records"] == 2
        assert result["invalid_records"] == 0
    
    def test_validate_dataset_file_invalid(self, tmp_path, sample_schema_path, invalid_yield_row):
        df = pd.DataFrame([invalid_yield_row])
        data_path = tmp_path / "test_data.parquet"
        df.to_parquet(data_path)
        
        with pytest.raises(ValidationError):
            validate_dataset_file(data_path, sample_schema_path)