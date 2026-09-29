"""
Unit tests for schema validation logic in utils/validation.py.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml

from utils.validation import (
    load_schema_from_yaml,
    schema_to_pydantic_model,
    validate_config,
    validate_output,
)
from utils.logging import ValidationFailedError


# Helper to create temporary schema and data files
def create_temp_file(content: Dict[str, Any], suffix: str) -> Path:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        if suffix in ['.yaml', '.yml']:
            yaml.dump(content, f)
        else:
            json.dump(content, f)
    return Path(path)


@pytest.fixture
def config_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "HF_API_KEY": {"type": "string"},
            "RANDOM_SEED": {"type": "integer"},
            "MAX_ATTEMPTS": {"type": "integer", "default": 400},
            "MIN_VALID_FUNCTIONS": {"type": "integer", "default": 100},
        },
        "required": ["HF_API_KEY", "RANDOM_SEED"]
    }


@pytest.fixture
def output_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "hash": {"type": "string"},
            "loc": {"type": "integer"},
            "metrics": {"type": "object"},
        },
        "required": ["code", "hash", "loc"]
    }


def test_load_schema_from_yaml(config_schema):
    schema_path = create_temp_file(config_schema, '.yaml')
    try:
        loaded = load_schema_from_yaml(schema_path)
        assert loaded["properties"]["HF_API_KEY"]["type"] == "string"
    finally:
        schema_path.unlink()


def test_schema_to_pydantic_model_config(config_schema):
    Model = schema_to_pydantic_model(config_schema, "TestConfig")
    # Valid data
    instance = Model(HF_API_KEY="secret123", RANDOM_SEED=42)
    assert instance.HF_API_KEY == "secret123"
    assert instance.RANDOM_SEED == 42
    assert instance.MAX_ATTEMPTS == 400 # default
    
    # Invalid data (missing required)
    with pytest.raises(Exception): # Pydantic ValidationError
        Model(HF_API_KEY="secret123") # Missing RANDOM_SEED


def test_schema_to_pydantic_model_output(output_schema):
    Model = schema_to_pydantic_model(output_schema, "TestOutput")
    instance = Model(code="def foo(): pass", hash="abc123", loc=1)
    assert instance.code == "def foo(): pass"
    assert instance.loc == 1


def test_validate_config_success(config_schema):
    schema_path = create_temp_file(config_schema, '.yaml')
    config_data = {"HF_API_KEY": "key123", "RANDOM_SEED": 12345}
    config_path = create_temp_file(config_data, '.json')
    
    try:
        result = validate_config(config_path, schema_path)
        assert result["HF_API_KEY"] == "key123"
        assert result["RANDOM_SEED"] == 12345
    finally:
        schema_path.unlink()
        config_path.unlink()


def test_validate_config_failure(config_schema):
    schema_path = create_temp_file(config_schema, '.yaml')
    config_data = {"RANDOM_SEED": 12345} # Missing HF_API_KEY
    config_path = create_temp_file(config_data, '.json')
    
    try:
        with pytest.raises(ValidationFailedError):
            validate_config(config_path, schema_path)
    finally:
        schema_path.unlink()
        config_path.unlink()


def test_validate_output_success(output_schema):
    schema_path = create_temp_file(output_schema, '.yaml')
    output_data = {"code": "x=1", "hash": "xyz", "loc": 1, "metrics": {}}
    output_path = create_temp_file(output_data, '.json')
    
    try:
        result = validate_output(output_path, schema_path)
        assert result["code"] == "x=1"
        assert result["hash"] == "xyz"
    finally:
        schema_path.unlink()
        output_path.unlink()


def test_validate_output_failure(output_schema):
    schema_path = create_temp_file(output_schema, '.yaml')
    output_data = {"code": "x=1"} # Missing hash and loc
    output_path = create_temp_file(output_data, '.json')
    
    try:
        with pytest.raises(ValidationFailedError):
            validate_output(output_path, schema_path)
    finally:
        schema_path.unlink()
        output_path.unlink()
