import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
import yaml

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.validate_schemas import (
    load_schema,
    validate_data_schema,
    validate_model_output_schema,
    validate_all_outputs
)

@pytest.fixture
def sample_dataset_schema():
    return {
        "required_columns": ["condition", "recall", "bizarreness", "participant_id"],
        "columns": {
            "condition": {
                "type": "string",
                "enum": ["strict (complete isolation)", "moderate (partial sensory reduction)", "partial (minimal sensory reduction)"]
            },
            "recall": {
                "type": "integer",
                "min": 0,
                "max": 1
            },
            "bizarreness": {
                "type": "integer",
                "min": 1,
                "max": 7
            },
            "participant_id": {
                "type": "string"
            }
        }
    }

@pytest.fixture
def sample_model_output_schema():
    return {
        "required_keys": ["model_type", "fixed_effects", "p_values", "metadata"],
        "keys": {
            "model_type": {"type": "string"},
            "fixed_effects": {"type": "list", "item_schema": {"type": "dict"}},
            "p_values": {"type": "dict"},
            "metadata": {"type": "dict"}
        }
    }

def test_validate_data_schema_valid(sample_dataset_schema):
    """Test validation with a valid dataset."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            "condition": ["strict (complete isolation)", "moderate (partial sensory reduction)"],
            "recall": [1, 0],
            "bizarreness": [5, 3],
            "participant_id": ["P001", "P002"]
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = validate_data_schema(temp_path, sample_dataset_schema)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["row_count"] == 2
    finally:
        os.unlink(temp_path)

def test_validate_data_schema_missing_column(sample_dataset_schema):
    """Test validation with a missing required column."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            "condition": ["strict (complete isolation)"],
            "recall": [1],
            "participant_id": ["P001"]
            # Missing "bizarreness"
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = validate_data_schema(temp_path, sample_dataset_schema)
        assert result["valid"] is False
        assert any("bizarreness" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)

def test_validate_data_schema_invalid_values(sample_dataset_schema):
    """Test validation with invalid enum values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            "condition": ["invalid_condition"],
            "recall": [1],
            "bizarreness": [5],
            "participant_id": ["P001"]
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = validate_data_schema(temp_path, sample_dataset_schema)
        assert result["valid"] is False
        assert any("invalid values" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)

def test_validate_data_schema_null_required(sample_dataset_schema):
    """Test validation with null values in required column."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            "condition": [None],
            "recall": [1],
            "bizarreness": [5],
            "participant_id": ["P001"]
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = validate_data_schema(temp_path, sample_dataset_schema)
        assert result["valid"] is False
        assert any("null values" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)

def test_validate_model_output_schema_valid(sample_model_output_schema):
    """Test validation with a valid model output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "model_type": "logistic_mixed",
            "fixed_effects": [{"term": "condition", "estimate": 0.5}],
            "p_values": {"condition": 0.03},
            "metadata": {"version": "1.0"}
        }
        json.dump(data, f)
        temp_path = f.name

    try:
        result = validate_model_output_schema(temp_path, sample_model_output_schema)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    finally:
        os.unlink(temp_path)

def test_validate_model_output_schema_missing_key(sample_model_output_schema):
    """Test validation with a missing required key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = {
            "model_type": "logistic_mixed",
            # Missing "fixed_effects"
            "p_values": {"condition": 0.03},
            "metadata": {"version": "1.0"}
        }
        json.dump(data, f)
        temp_path = f.name

    try:
        result = validate_model_output_schema(temp_path, sample_model_output_schema)
        assert result["valid"] is False
        assert any("fixed_effects" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)

def test_validate_model_output_schema_invalid_json():
    """Test validation with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = f.name

    try:
        schema = {"required_keys": ["model_type"]}
        result = validate_model_output_schema(temp_path, schema)
        assert result["valid"] is False
        assert any("Invalid JSON" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)

def test_file_not_found():
    """Test validation with non-existent file."""
    schema = {"required_columns": ["test"]}
    result = validate_data_schema("/non/existent/file.csv", schema)
    assert result["valid"] is False
    assert any("not found" in error for error in result["errors"])

def test_unsupported_file_format():
    """Test validation with unsupported file format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        schema = {"required_columns": ["test"]}
        result = validate_data_schema(temp_path, schema)
        assert result["valid"] is False
        assert any("Unsupported file format" in error for error in result["errors"])
    finally:
        os.unlink(temp_path)