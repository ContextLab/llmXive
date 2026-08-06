"""
Unit tests for the contract validator.
"""
import json
import tempfile
from pathlib import Path
import pytest

from code.data.contract_validator import (
    validate_dataset_schema,
    validate_output_schema,
    load_schema,
    validate_type,
    validate_required,
    validate_properties
)

# Sample valid data for dataset schema
VALID_DATASET = {
    "metadata": {
        "source_dataset": "TransitLM-v1",
        "cities": ["Beijing", "Shanghai"],
        "vocabulary_size": 1000,
        "total_routes": 500,
        "stratification_counts": {
            "short": 200,
            "medium": 200,
            "long": 100
        },
        "unknown_token": "<UNKNOWN>",
        "checksum": "a" * 64
    },
    "routes": [
        {
            "route_id": "R001",
            "city": "Beijing",
            "stops": ["A", "B", "C"],
            "length": 3,
            "category": "short",
            "has_unknown": False
        }
    ]
}

# Sample invalid data for dataset schema (missing required field)
INVALID_DATASET = {
    "metadata": {
        "source_dataset": "TransitLM-v1",
        "cities": ["Beijing"],
        # missing other required fields
    },
    "routes": []
}

# Sample valid data for output schema
VALID_OUTPUT = {
    "evaluation_metrics": {
        "lightweight_model": {
            "category_scores": {
                "short": {"validity_rate": 0.9, "sample_count": 100, "confidence_interval": [0.85, 0.95]},
                "medium": {"validity_rate": 0.8, "sample_count": 100, "confidence_interval": [0.75, 0.85]},
                "long": {"validity_rate": 0.6, "sample_count": 100, "confidence_interval": [0.55, 0.65]}
            },
            "overall_validity": {"validity_rate": 0.76, "sample_count": 300}
        },
        "baseline_model": {
            "category_scores": {
                "short": {"validity_rate": 0.95, "sample_count": 100, "confidence_interval": [0.90, 1.0]},
                "medium": {"validity_rate": 0.90, "sample_count": 100, "confidence_interval": [0.85, 0.95]},
                "long": {"validity_rate": 0.85, "sample_count": 100, "confidence_interval": [0.80, 0.90]}
            },
            "overall_validity": {"validity_rate": 0.90, "sample_count": 300}
        },
        "comparison": {
            "validity_gap": {"1": 0.05, "20": 0.05},
            "inflection_point": 25,
            "high_risk_threshold": 30
        }
    },
    "statistical_analysis": {
        "survival_analysis": {
            "curves": {
                "lightweight": {
                    "times": [1, 2, 3],
                    "survival_probabilities": [1.0, 0.9, 0.8],
                    "confidence_intervals": [[1.0, 1.0], [0.85, 0.95], [0.75, 0.85]]
                },
                "baseline": {
                    "times": [1, 2, 3],
                    "survival_probabilities": [1.0, 0.95, 0.9],
                    "confidence_intervals": [[1.0, 1.0], [0.90, 1.0], [0.85, 0.95]]
                }
            },
            "median_survival_time": {"lightweight": 10.5, "baseline": 15.2}
        },
        "chi_squared_scan": {
            "results": [
                {"length": 1, "chi2_statistic": 1.2, "p_value": 0.27, "is_significant": False}
            ],
            "significant_lengths": [],
            "bonferroni_adjusted_alpha": 0.001
        },
        "log_rank_test": {
            "statistic": 5.6,
            "p_value": 0.018,
            "is_significant": True
        }
    }
}

def test_validate_type():
    assert validate_type(123, "integer") is True
    assert validate_type(123.45, "integer") is False
    assert validate_type("hello", "string") is True
    assert validate_type(["a", "b"], "array") is True
    assert validate_type({"a": 1}, "object") is True
    assert validate_type(True, "boolean") is True
    assert validate_type(None, "null") is True
    assert validate_type(False, "boolean") is True

def test_validate_required():
    data = {"a": 1, "b": 2}
    assert validate_required(data, ["a", "b"]) == []
    assert validate_required(data, ["a", "c"]) == ["Missing required field 'c' at root"]

def test_validate_dataset_schema_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(VALID_DATASET, f)
        temp_path = Path(f.name)
    
    # We need the schema file to exist relative to the temp file's parent structure
    # For this unit test, we assume the schema is in the repo
    schema_path = Path("data/contracts/dataset.schema.yaml")
    if not schema_path.exists():
        # Fallback: create a temporary schema for the test if not found in repo
        # In CI, the file should exist
        pytest.skip("Schema file not found in repo, skipping integration-style test")
    
    is_valid, errors = validate_dataset_schema(temp_path, schema_path)
    assert is_valid is True
    assert errors == []
    temp_path.unlink()

def test_validate_dataset_schema_invalid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(INVALID_DATASET, f)
        temp_path = Path(f.name)
    
    schema_path = Path("data/contracts/dataset.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found in repo, skipping integration-style test")

    is_valid, errors = validate_dataset_schema(temp_path, schema_path)
    assert is_valid is False
    assert len(errors) > 0
    temp_path.unlink()

def test_validate_output_schema_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(VALID_OUTPUT, f)
        temp_path = Path(f.name)
    
    schema_path = Path("data/contracts/output.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found in repo, skipping integration-style test")

    is_valid, errors = validate_output_schema(temp_path, schema_path)
    assert is_valid is True
    assert errors == []
    temp_path.unlink()