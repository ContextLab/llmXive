import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml

from code.data.validator import (
    load_schema,
    validate_dataframe_against_schema,
    validate_input_schema,
    validate_output_schema,
    validate_parsed_data
)

# Fixtures
@pytest.fixture
def sample_output_df():
    """Create a valid sample DataFrame matching output schema."""
    data = {
        "discharge_id": [12345, 12346],
        "island_width": [0.05, 0.06],
        "tau_e": [0.5, 0.6],
        "confinement_mode": ["L-mode", "H-mode"],
        "h98y2": [0.7, 1.1],
        "te_profile": [[1, 2], [3, 4]],
        "ne_profile": [[0.1, 0.2], [0.3, 0.4]],
        "resonant_surface_density": [2.0, 3.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_invalid_df():
    """Create an invalid DataFrame (missing required column)."""
    data = {
        "discharge_id": [12345],
        "island_width": [0.05],
        # Missing tau_e and confinement_mode
        "h98y2": [0.7]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_raw_data():
    return {
        "discharge_id": 12345,
        "fields": {
            "efit": {"q_profile": [1.0, 2.0]},
            "islands": {"width": 0.05},
            "taue": {"value": 0.5},
            "h98y2": 0.9
        }
    }

@pytest.fixture
def schema_dir(tmp_path):
    """Create temporary schema files."""
    # Create dataset.schema.yaml
    dataset_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["discharge_id", "fields"],
        "properties": {
            "discharge_id": {"type": "integer"},
            "fields": {"type": "object"}
        }
    }
    dataset_path = tmp_path / "dataset.schema.yaml"
    with open(dataset_path, 'w') as f:
        yaml.dump(dataset_schema, f)
    
    # Create output.schema.yaml
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["discharge_id", "island_width", "tau_e", "confinement_mode"],
        "properties": {
            "discharge_id": {"properties": {"type": {"enum": ["integer"]}}},
            "island_width": {"properties": {"type": {"enum": ["number"]}}},
            "tau_e": {"properties": {"type": {"enum": ["number"]}}},
            "confinement_mode": {"properties": {"type": {"enum": ["string"]}}},
            "te_profile": {"properties": {"type": {"enum": ["array"]}}}
        }
    }
    output_path = tmp_path / "output.schema.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(output_schema, f)
        
    return tmp_path, dataset_path, output_path

class TestValidator:
    def test_load_schema_valid(self, schema_dir):
        _, _, output_path = schema_dir
        schema = load_schema(output_path)
        assert "required" in schema
        assert "properties" in schema

    def test_load_schema_not_found(self, schema_dir):
        _, _, _ = schema_dir
        fake_path = Path("/nonexistent/schema.yaml")
        with pytest.raises(FileNotFoundError):
            load_schema(fake_path)

    def test_validate_output_schema_valid(self, sample_output_df, schema_dir):
        _, _, output_path = schema_dir
        is_valid, errors = validate_output_schema(sample_output_df, output_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_output_schema_missing_columns(self, sample_invalid_df, schema_dir):
        _, _, output_path = schema_dir
        is_valid, errors = validate_output_schema(sample_invalid_df, output_path)
        assert is_valid is False
        # Should detect missing required columns
        assert any("Missing required columns" in err for err in errors)

    def test_validate_input_schema_valid(self, sample_raw_data, schema_dir):
        _, dataset_path, _ = schema_dir
        is_valid, errors = validate_input_schema(sample_raw_data, dataset_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_input_schema_missing_id(self, schema_dir):
        _, dataset_path, _ = schema_dir
        bad_data = {"fields": {}}
        is_valid, errors = validate_input_schema(bad_data, dataset_path)
        assert is_valid is False
        assert any("Missing 'discharge_id'" in err for err in errors)

    def test_validate_parsed_data_full(self, sample_output_df, schema_dir):
        _, dataset_path, output_path = schema_dir
        is_valid, errors = validate_parsed_data(sample_output_df, dataset_path, output_path)
        assert is_valid is True
        assert len(errors) == 0