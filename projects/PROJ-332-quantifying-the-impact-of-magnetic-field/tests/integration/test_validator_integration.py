import pytest
import pandas as pd
import yaml
import json
import tempfile
import os
from pathlib import Path

from code.data.validator import validate_input_schema, validate_output_schema


def create_temp_schema_file(content: dict) -> str:
    fd, path = tempfile.mkstemp(suffix='.yaml')
    with os.fdopen(fd, 'w') as f:
        yaml.dump(content, f)
    return path


@pytest.fixture
def sample_input_schema():
    return {
        "type": "object",
        "properties": {
            "discharge_id": {"type": "integer"},
            "island_width": {"type": "number"},
            "tau_e": {"type": "number"},
            "te_profile": {"type": "array"},
            "ne_profile": {"type": "array"},
            "confinement_mode": {"type": "string"}
        },
        "required": ["discharge_id", "island_width", "tau_e", "confinement_mode"]
    }


@pytest.fixture
def sample_output_schema():
    return {
        "type": "object",
        "properties": {
            "discharge_id": {"type": "integer"},
            "resonant_surface_density": {"type": "number"},
            "island_width": {"type": "number"},
            "tau_e": {"type": "number"},
            "correlation_coefficient": {"type": "number"},
            "p_value": {"type": "number"}
        },
        "required": ["discharge_id", "resonant_surface_density", "tau_e"]
    }


def test_validate_input_schema_integration(sample_input_schema):
    path = create_temp_schema_file(sample_input_schema)
    try:
        df = pd.DataFrame({
            "discharge_id": [12345, 12346],
            "island_width": [0.05, 0.06],
            "tau_e": [1.2, 1.3],
            "te_profile": [[1, 2], [3, 4]],
            "ne_profile": [[10, 20], [30, 40]],
            "confinement_mode": ["L-mode", "H-mode"]
        })
        
        is_valid, errors = validate_input_schema(df, path)
        
        assert is_valid
        assert len(errors) == 0
    finally:
        os.remove(path)


def test_validate_input_schema_missing_column(sample_input_schema):
    path = create_temp_schema_file(sample_input_schema)
    try:
        # Missing 'confinement_mode' which is required
        df = pd.DataFrame({
            "discharge_id": [12345],
            "island_width": [0.05],
            "tau_e": [1.2],
            "te_profile": [[1, 2]],
            "ne_profile": [[10, 20]]
        })
        
        is_valid, errors = validate_input_schema(df, path)
        
        assert not is_valid
        assert any("confinement_mode" in e for e in errors)
    finally:
        os.remove(path)


def test_validate_output_schema_integration(sample_output_schema):
    path = create_temp_schema_file(sample_output_schema)
    try:
        df = pd.DataFrame({
            "discharge_id": [12345],
            "resonant_surface_density": 0.8,
            "island_width": 0.05,
            "tau_e": 1.2,
            "correlation_coefficient": -0.45,
            "p_value": 0.03
        })
        
        is_valid, errors = validate_output_schema(df, path)
        
        assert is_valid
        assert len(errors) == 0
    finally:
        os.remove(path)


def test_validate_output_schema_wrong_type(sample_output_schema):
    path = create_temp_schema_file(sample_output_schema)
    try:
        df = pd.DataFrame({
            "discharge_id": [12345],
            "resonant_surface_density": "high",  # Should be number
            "island_width": 0.05,
            "tau_e": 1.2
        })
        
        is_valid, errors = validate_output_schema(df, path)
        
        assert not is_valid
        assert any("invalid type" in e for e in errors)
    finally:
        os.remove(path)
