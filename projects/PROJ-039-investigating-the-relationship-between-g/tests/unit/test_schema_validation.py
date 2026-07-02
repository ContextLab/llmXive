import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import SchemaValidator, validate_artifacts

@pytest.fixture
def sample_microbiome_data():
    return {
        "subject_id": "sub_001",
        "metadata": {
            "age": 25.0,
            "sex": "M",
            "bmi": 22.5
        },
        "taxa_abundances": {
            "Bacteroides": 0.3,
            "Firmicutes": 0.5
        }
    }

@pytest.fixture
def sample_eeg_data():
    return {
        "subject_id": "sub_002",
        "metadata": {
            "age": 30.0,
            "sex": "F",
            "bmi": 24.0
        },
        "eeg_metrics": {
            "alpha_power": 12.5,
            "valid_epochs": 150
        }
    }

@pytest.fixture
def sample_matched_pairs():
    return {
        "pairs": [
            {
                "microbiome_subject_id": "sub_001",
                "eeg_subject_id": "sub_002",
                "distance": 0.05
            }
        ],
        "metadata": {
            "method": "nearest_neighbor",
            "total_pairs": 1,
            "path_selected": "Path A"
        }
    }

@pytest.fixture
def sample_analysis_results():
    return {
        "path_type": "Path A",
        "statistics": {
            "correlation": 0.45,
            "p_value": 0.01
        },
        "permutation_test": {
            "passed": True,
            "p_value": 0.02
        },
        "disclaimer": "Note: This analysis is associational only; no causal inference is made."
    }

@pytest.fixture
def schema_validator():
    return SchemaValidator("contracts/dataset.schema.yaml")

def test_validate_microbiome_data(schema_validator, sample_microbiome_data):
    assert schema_validator.validate(sample_microbiome_data) is True

def test_validate_eeg_data(schema_validator, sample_eeg_data):
    assert schema_validator.validate(sample_eeg_data) is True

def test_validate_invalid_data(schema_validator):
    invalid_data = {
        "subject_id": 123,  # Should be string
        "metadata": "bad",   # Should be object
        "taxa_abundances": {}
    }
    with pytest.raises((TypeError, Exception)):
        schema_validator.validate(invalid_data)

def test_validate_matched_pairs(sample_matched_pairs):
    validator = SchemaValidator("contracts/output.schema.yaml")
    assert validator.validate(sample_matched_pairs) is True

def test_validate_analysis_results(sample_analysis_results):
    validator = SchemaValidator("contracts/output.schema.yaml")
    assert validator.validate(sample_analysis_results) is True

def test_missing_schema_file():
    with pytest.raises(FileNotFoundError):
        SchemaValidator("contracts/non_existent_schema.yaml")

def test_load_schema_from_path():
    validator = SchemaValidator()
    validator.load_schema("contracts/dataset.schema.yaml")
    assert validator.schema is not None
    assert "definitions" in validator.schema

def test_validate_artifacts_matched_pairs(sample_matched_pairs):
    result = validate_artifacts([sample_matched_pairs], "matched_pairs")
    assert result is True

def test_validate_artifacts_analysis(sample_analysis_results):
    result = validate_artifacts([sample_analysis_results], "analysis_results")
    assert result is True