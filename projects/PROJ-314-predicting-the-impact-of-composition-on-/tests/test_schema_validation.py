"""
Tests for schema validation logic.
"""
import pytest
import yaml
import tempfile
import os
from pathlib import Path
from code.contracts.validate_schemas import validate_model_result_schema, validate_ceramic_entry_schema, load_yaml_schema

def test_validate_model_result_schema_valid():
    """Test validation with a correctly formed model_result schema."""
    schema_content = {
        "type": "object",
        "properties": {
            "model_type": {"type": "string"},
            "mae": {"type": "number"},
            "r_squared": {"type": "number"},
            "feature_importance_ranking": {"type": "array"},
            "cv_stability_scores": {"type": "object"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        temp_path = f.name
    
    try:
        result = validate_model_result_schema(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_validate_model_result_schema_missing_field():
    """Test validation fails when a required field is missing."""
    schema_content = {
        "type": "object",
        "properties": {
            "model_type": {"type": "string"},
            "mae": {"type": "number"}
            # Missing r_squared, feature_importance_ranking, cv_stability_scores
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError) as excinfo:
            validate_model_result_schema(temp_path)
        assert "missing required fields" in str(excinfo.value)
    finally:
        os.unlink(temp_path)

def test_validate_model_result_schema_missing_type():
    """Test validation fails when a field has no type."""
    schema_content = {
        "type": "object",
        "properties": {
            "model_type": {"type": "string"},
            "mae": {"type": "number"},
            "r_squared": {"type": "number"},
            "feature_importance_ranking": {}, # Missing type
            "cv_stability_scores": {"type": "object"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError) as excinfo:
            validate_model_result_schema(temp_path)
        assert "missing a 'type' definition" in str(excinfo.value)
    finally:
        os.unlink(temp_path)

def test_validate_ceramic_entry_schema():
    """Test validation of ceramic entry schema structure."""
    schema_content = {
        "type": "object",
        "properties": {
            "composition": {"type": "string"},
            "weibull_modulus": {"type": "number"}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        temp_path = f.name
    
    try:
        result = validate_ceramic_entry_schema(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)
