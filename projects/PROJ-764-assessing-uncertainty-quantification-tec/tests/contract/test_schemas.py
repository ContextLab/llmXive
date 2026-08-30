"""
Contract tests for validating data schemas against YAML definitions.
Ensures that data artifacts conform to the expected structure.
"""
import json
import yaml
import pandas as pd
from pathlib import Path
import pytest
from typing import Dict, Any, List

# Base path for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "code" / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Basic validation of data against a JSON schema structure.
    Note: This is a simplified validator. For production, use `jsonschema` library.
    """
    # Check type
    expected_type = schema.get("type")
    if expected_type == "object" and not isinstance(data, dict):
        return False
    
    # Check required fields
    required = schema.get("required", [])
    if isinstance(data, dict):
        for field in required:
            if field not in data:
                return False
    
    # Check properties if data is a dict
    properties = schema.get("properties", {})
    if isinstance(data, dict):
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")
                
                # Handle null types
                if prop_type == "null":
                    if value is not None:
                        return False
                elif prop_type == "number":
                    if not isinstance(value, (int, float)) and value is not None:
                        return False
                elif prop_type == "integer":
                    if not isinstance(value, int) and value is not None:
                        return False
                elif prop_type == "string":
                    if not isinstance(value, str) and value is not None:
                        return False
                elif prop_type == "array":
                    if not isinstance(value, list) and value is not None:
                        return False
                elif prop_type == "boolean":
                    if not isinstance(value, bool) and value is not None:
                        return False
                
                # Check enum if present
                if "enum" in prop_schema and value is not None:
                    if value not in prop_schema["enum"]:
                        return False
    return True

class TestMaterialSampleSchema:
    """Tests for material_sample.schema.yaml compliance."""

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        assert (CONTRACTS_DIR / "material_sample.schema.yaml").exists()

    def test_validate_sample_data(self):
        """Test validation with a mock material sample record."""
        schema = load_schema("material_sample.schema.yaml")
        
        valid_sample = {
            "sample_id": 12345,
            "composition": "Li2O",
            "formation_energy_per_atom": -2.34,
            "structure": {
                "lattice_vectors": [
                    [3.0, 0.0, 0.0],
                    [0.0, 3.0, 0.0],
                    [0.0, 0.0, 3.0]
                ],
                "atomic_numbers": [3, 3, 8],
                "fractional_coordinates": [
                    [0.0, 0.0, 0.0],
                    [0.5, 0.5, 0.5],
                    [0.25, 0.25, 0.25]
                ]
            }
        }
        
        assert validate_json_against_schema(valid_sample, schema) is True

    def test_validate_missing_required_field(self):
        """Test validation fails when a required field is missing."""
        schema = load_schema("material_sample.schema.yaml")
        
        invalid_sample = {
            "sample_id": 12345,
            "composition": "Li2O",
            # Missing formation_energy_per_atom
            "structure": {
                "lattice_vectors": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
                "atomic_numbers": [3, 3, 8],
                "fractional_coordinates": [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]]
            }
        }
        
        assert validate_json_against_schema(invalid_sample, schema) is False

class TestUQPredictionSchema:
    """Tests for uq_prediction.schema.yaml compliance."""

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        assert (CONTRACTS_DIR / "uq_prediction.schema.yaml").exists()

    def test_validate_prediction_record(self):
        """Test validation with a mock UQ prediction record."""
        schema = load_schema("uq_prediction.schema.yaml")
        
        valid_prediction = {
            "sample_id": 12345,
            "method": "DeepEnsemble",
            "prediction": -2.34,
            "variance": 0.05,
            "lower_50": -2.40,
            "upper_50": -2.28,
            "lower_90": -2.45,
            "upper_90": -2.23,
            "aleatoric": 0.02,
            "epistemic": 0.03,
            "total": 0.05,
            "uncertainty_type": "decomposed"
        }
        
        assert validate_json_against_schema(valid_prediction, schema) is True

    def test_validate_sparse_gp_nulls(self):
        """Test validation for SparseGP where aleatoric/epistemic are null."""
        schema = load_schema("uq_prediction.schema.yaml")
        
        sparse_gp_prediction = {
            "sample_id": 12345,
            "method": "SparseGP",
            "prediction": -2.34,
            "variance": 0.05,
            "lower_50": -2.40,
            "upper_50": -2.28,
            "lower_90": -2.45,
            "upper_90": -2.23,
            "aleatoric": None,
            "epistemic": None,
            "total": None,
            "uncertainty_type": None
        }
        
        assert validate_json_against_schema(sparse_gp_prediction, schema) is True

    def test_validate_invalid_method(self):
        """Test validation fails for an invalid method name."""
        schema = load_schema("uq_prediction.schema.yaml")
        
        invalid_prediction = {
            "sample_id": 12345,
            "method": "UnknownMethod",
            "prediction": -2.34,
            "variance": 0.05,
            "lower_50": -2.40,
            "upper_50": -2.28,
            "lower_90": -2.45,
            "upper_90": -2.23,
            "aleatoric": 0.02,
            "epistemic": 0.03,
            "total": 0.05,
            "uncertainty_type": "decomposed"
        }
        
        assert validate_json_against_schema(invalid_prediction, schema) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])