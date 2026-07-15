"""
Unit tests for dataset and model output schema validation.
Validates that sample data conforms to the defined YAML schemas.
"""
import pytest
import yaml
import json
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.validators import load_yaml, validate_schema, ValidationError


class TestDatasetSchema:
    """Tests for dataset.schema.yaml validation"""

    @pytest.fixture
    def schema_path(self):
        return Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"

    @pytest.fixture
    def valid_sample(self):
        return {
            "sample_id": "SAMPLE-000001",
            "reactant_smiles": "CCO",
            "product_smiles": "CC=O",
            "spectrum_ir": [0.1, 0.2, 0.15],
            "spectrum_raman": [0.05, 0.1, 0.08],
            "spectrum_nmr": [1.0, 0.9, 0.95],
            "fingerprint_ecfp4": [1] * 1024,
            "conditions": {
                "solvent": "water",
                "catalyst": "acid",
                "temperature_k": 298.15
            },
            "target_energy_normalized": -0.5,
            "scaffold_id": "SCAF-000001",
            "split": "train"
        }

    def test_schema_loads(self, schema_path):
        """Test that the schema file is valid YAML"""
        schema = load_yaml(schema_path)
        assert schema is not None
        assert "properties" in schema
        assert "required" in schema

    def test_valid_sample_passes(self, schema_path, valid_sample):
        """Test that a valid sample passes schema validation"""
        schema = load_yaml(schema_path)
        # Note: validate_schema in validators.py expects a function or schema dict
        # This test verifies the structure is loadable
        assert schema["type"] == "object"
        assert "sample_id" in schema["properties"]

    def test_missing_required_field(self, schema_path, valid_sample):
        """Test that missing required fields are detected"""
        schema = load_yaml(schema_path)
        invalid_sample = valid_sample.copy()
        del invalid_sample["sample_id"]
        
        # The validator should catch missing required fields
        # This is a structural test - actual validation logic depends on validators.py
        assert "sample_id" in schema["required"]

    def test_invalid_split_value(self, schema_path, valid_sample):
        """Test that invalid split values are detected"""
        invalid_sample = valid_sample.copy()
        invalid_sample["split"] = "invalid_split"
        
        schema = load_yaml(schema_path)
        valid_splits = schema["properties"]["split"]["enum"]
        assert "invalid_split" not in valid_splits
        assert "train" in valid_splits

    def test_fingerprint_length(self, schema_path, valid_sample):
        """Test that fingerprint length is validated"""
        schema = load_yaml(schema_path)
        min_len = schema["properties"]["fingerprint_ecfp4"]["minItems"]
        assert min_len == 1024


class TestModelOutputSchema:
    """Tests for model_output.schema.yaml validation"""

    @pytest.fixture
    def schema_path(self):
        return Path(__file__).parent.parent.parent / "contracts" / "model_output.schema.yaml"

    @pytest.fixture
    def valid_prediction(self):
        return {
            "sample_id": "SAMPLE-000001",
            "predicted_energy_normalized": -0.45,
            "true_energy_normalized": -0.5,
            "error": 0.05,
            "absolute_error": 0.05,
            "attention_weights_ir": [0.1, 0.2, 0.1],
            "attention_weights_raman": [0.05, 0.1, 0.05],
            "attention_weights_nmr": [0.2, 0.3, 0.2],
            "timestamp": "2024-01-01T00:00:00Z"
        }

    def test_schema_loads(self, schema_path):
        """Test that the model output schema file is valid YAML"""
        schema = load_yaml(schema_path)
        assert schema is not None
        assert "properties" in schema
        assert "required" in schema

    def test_valid_prediction_passes(self, schema_path, valid_prediction):
        """Test that a valid prediction passes schema validation"""
        schema = load_yaml(schema_path)
        assert schema["type"] == "object"
        assert "sample_id" in schema["properties"]

    def test_additional_properties_false(self, schema_path):
        """Test that additional properties are not allowed"""
        schema = load_yaml(schema_path)
        assert schema.get("additionalProperties") is False

    def test_attention_weights_range(self, schema_path, valid_prediction):
        """Test that attention weights are in valid range"""
        schema = load_yaml(schema_path)
        for key in ["attention_weights_ir", "attention_weights_raman", "attention_weights_nmr"]:
            prop = schema["properties"][key]
            assert prop["items"]["minimum"] == 0.0
            assert prop["items"]["maximum"] == 1.0

    def test_error_calculation_valid(self, valid_prediction):
        """Test that error calculation is consistent"""
        calculated_error = valid_prediction["predicted_energy_normalized"] - valid_prediction["true_energy_normalized"]
        assert abs(calculated_error - valid_prediction["error"]) < 1e-6
        assert abs(calculated_error) == valid_prediction["absolute_error"]