"""
Contract test for the Model Results schema.
Validates that model output conforms to the JSON schema defined in contracts/.
"""
import pytest
import json
import yaml
from pathlib import Path

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

@pytest.fixture
def model_results_schema():
    """Load the model results schema."""
    schema_path = Path(__file__).parent.parent.parent / "contracts" / "model_results.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def test_valid_model_results(sample_model_results, model_results_schema):
    """Test that valid model results pass schema validation."""
    try:
        validate(instance=sample_model_results, schema=model_results_schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_missing_pvr_results(sample_model_results, model_results_schema):
    """Test that missing 'pvr_results' fails validation."""
    invalid_data = sample_model_results.copy()
    del invalid_data["pvr_results"]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=model_results_schema)

def test_invalid_cv_r2_mean(sample_model_results, model_results_schema):
    """Test that non-numeric R2 mean fails validation."""
    invalid_data = sample_model_results.copy()
    invalid_data["cross_validation"]["r2_mean"] = "0.75"
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=model_results_schema)

def test_p_value_out_of_range(sample_model_results, model_results_schema):
    """Test that p-value > 1 fails validation."""
    invalid_data = sample_model_results.copy()
    invalid_data["pvr_results"]["p_value"] = 1.5
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=model_results_schema)

def test_negative_permutation_iterations(sample_model_results, model_results_schema):
    """Test that negative permutation iterations fails validation."""
    invalid_data = sample_model_results.copy()
    invalid_data["permutation_test"]["iterations"] = -10
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=model_results_schema)
