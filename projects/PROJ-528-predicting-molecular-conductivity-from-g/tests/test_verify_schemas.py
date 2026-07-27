"""
Unit tests for T050: Schema Verification.
These tests ensure the verification logic correctly identifies valid and invalid schemas.
"""

import pytest
import json
import os
import tempfile
import yaml
from code.verify_schemas import (
    validate_type,
    validate_array_items,
    validate_object_properties,
    load_schema,
    load_results
)

def test_validate_type_number():
    assert validate_type(10, "number", "test")[0] is True
    assert validate_type(10.5, "number", "test")[0] is True
    assert validate_type("10", "number", "test")[0] is False

def test_validate_type_string():
    assert validate_type("hello", "string", "test")[0] is True
    assert validate_type(123, "string", "test")[0] is False

def test_validate_type_array():
    assert validate_type([1, 2], "array", "test")[0] is True
    assert validate_type({}, "array", "test")[0] is False

def test_validate_array_items():
    schema = {"items": {"type": "number"}}
    valid, _ = validate_array_items([1, 2, 3], schema, "test")
    assert valid is True
    
    valid, msg = validate_array_items([1, "bad", 3], schema, "test")
    assert valid is False
    assert "test[1]" in msg

def test_validate_object_properties_required():
    schema = {
        "required": ["r2", "mae"],
        "properties": {
            "r2": {"type": "number"},
            "mae": {"type": "number"}
        }
    }
    data = {"r2": 0.5}
    valid, msg = validate_object_properties(data, schema, "root")
    assert valid is False
    assert "mae" in msg

def test_validate_object_properties_valid():
    schema = {
        "required": ["r2"],
        "properties": {
            "r2": {"type": "number", "minimum": -1, "maximum": 1}
        }
    }
    data = {"r2": 0.8}
    valid, msg = validate_object_properties(data, schema, "root")
    assert valid is True

def test_validate_object_properties_minimum_violation():
    schema = {
        "required": ["mae"],
        "properties": {
            "mae": {"type": "number", "minimum": 0.0}
        }
    }
    data = {"mae": -0.5}
    valid, msg = validate_object_properties(data, schema, "root")
    assert valid is False
    assert "below minimum" in msg

def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema("/nonexistent/path/schema.yaml")

def test_load_results_missing_file():
    with pytest.raises(FileNotFoundError):
        load_results("/nonexistent/path/results.json")

def test_integration_valid_data():
    """Simulate a valid model_results.json structure against the schema."""
    valid_data = {
        "r2": 0.85,
        "mae": 0.12,
        "cv_scores": [0.82, 0.84, 0.86, 0.83, 0.85],
        "sensitivity_data": [
            {"threshold": 3.0, "r2": 0.85, "kruskal_stat": 1.2, "kruskal_pval": 0.5}
        ],
        "vif_scores": [
            {"feature": "degree_mean", "vif": 2.5},
            {"feature": "path_length_mean", "vif": 3.1}
        ]
    }
    
    schema = {
        "type": "object",
        "required": ["r2", "mae", "cv_scores", "sensitivity_data", "vif_scores"],
        "properties": {
            "r2": {"type": "number"},
            "mae": {"type": "number"},
            "cv_scores": {"type": "array", "items": {"type": "number"}},
            "sensitivity_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["threshold", "r2", "kruskal_stat", "kruskal_pval"],
                    "properties": {
                        "threshold": {"type": "number"},
                        "r2": {"type": "number"},
                        "kruskal_stat": {"type": "number"},
                        "kruskal_pval": {"type": "number"}
                    }
                }
            },
            "vif_scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["feature", "vif"],
                    "properties": {
                        "feature": {"type": "string"},
                        "vif": {"type": "number"}
                    }
                }
            }
        }
    }
    
    valid, msg = validate_object_properties(valid_data, schema, "root")
    assert valid is True, f"Validation failed: {msg}"

def test_integration_invalid_data_missing_field():
    """Test detection of missing required field."""
    invalid_data = {
        "r2": 0.85,
        # missing mae
        "cv_scores": [0.82],
        "sensitivity_data": [],
        "vif_scores": []
    }
    
    schema = {
        "type": "object",
        "required": ["r2", "mae"],
        "properties": {
            "r2": {"type": "number"},
            "mae": {"type": "number"}
        }
    }
    
    valid, msg = validate_object_properties(invalid_data, schema, "root")
    assert valid is False
    assert "mae" in msg