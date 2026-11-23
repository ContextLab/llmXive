"""
Contract test for regression output schema (T008).
Validates that regression output JSON conforms to contracts/output.schema.yaml
using pydantic or jsonschema.
"""
import json
import os
import tempfile
from pathlib import Path
import yaml
import pytest
from pydantic import BaseModel, ValidationError, Field
from typing import Dict, Any, Optional
from datetime import datetime

# Define the Pydantic model matching contracts/output.schema.yaml
class RegressionOutput(BaseModel):
    model_name: str
    adjusted_alpha: float
    bonferroni_corrected_p_values: Dict[str, float]
    coefficients: Dict[str, float]
    vif_scores: Dict[str, float]
    sample_size: int
    clustering_variable: str
    generated_at: str

    @staticmethod
    def validate_from_file(file_path: str) -> bool:
        """Load a JSON file and validate against the schema."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        return RegressionOutput(**data) is not None

@pytest.fixture
def valid_output():
    return {
        "model_name": "Stability_Score",
        "adjusted_alpha": 0.0167,
        "bonferroni_corrected_p_values": {
            "CSA_Index": 0.005,
            "HFIAS": 0.12,
            "education": 0.03
        },
        "coefficients": {
            "CSA_Index": 0.45,
            "HFIAS": -0.12,
            "education": 0.08
        },
        "vif_scores": {
            "CSA_Index": 1.2,
            "HFIAS": 1.5,
            "education": 1.1
        },
        "sample_size": 500,
        "clustering_variable": "village_id",
        "generated_at": datetime.now().isoformat()
    }

@pytest.fixture
def schema_path():
    # Assuming the schema is at the project root relative to code/tests/contract/
    # Adjust path if necessary based on project structure
    return Path(__file__).parent.parent.parent.parent / "contracts" / "output.schema.yaml"

def test_schema_file_exists(schema_path):
    """Ensure the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_schema_is_valid_yaml(schema_path):
    """Ensure the schema file is valid YAML."""
    with open(schema_path, 'r') as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")

def test_valid_output_passes_validation(valid_output):
    """Test that a valid output dictionary passes validation."""
    try:
        RegressionOutput(**valid_output)
    except ValidationError as e:
        pytest.fail(f"Valid output failed validation: {e}")

def test_invalid_output_fails_validation():
    """Test that an invalid output dictionary fails validation."""
    invalid_output = {
        "model_name": 123,  # Should be string
        "adjusted_alpha": "high", # Should be float
        "bonferroni_corrected_p_values": {},
        "coefficients": {},
        "vif_scores": {},
        "sample_size": "many", # Should be int
        "clustering_variable": "village_id",
        "generated_at": "not-a-date"
    }
    with pytest.raises(ValidationError):
        RegressionOutput(**invalid_output)

def test_validate_from_file_with_valid_json(valid_output, schema_path):
    """Test validation against a temporary JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_output, f)
        temp_path = f.name

    try:
        result = RegressionOutput.validate_from_file(temp_path)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_validate_from_file_with_invalid_json(schema_path):
    """Test validation against a temporary invalid JSON file."""
    invalid_data = {"model_name": 123}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(invalid_data, f)
        temp_path = f.name

    try:
        with pytest.raises(ValidationError):
            RegressionOutput.validate_from_file(temp_path)
    finally:
        os.unlink(temp_path)
