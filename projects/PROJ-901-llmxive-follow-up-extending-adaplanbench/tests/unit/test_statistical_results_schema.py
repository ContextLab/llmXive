import json
import os
import pytest
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError

from config import Paths

def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema from a YAML file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        # YAML is a superset of JSON, so we can load it directly
        return yaml.safe_load(f)

def load_json(file_path: Path) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def schema_path():
    """Path to the statistical results schema."""
    return Path("contracts/statistical-results.schema.yaml")

@pytest.fixture
def results_path():
    """Path to the statistical results JSON."""
    paths = Paths()
    return paths.data_processed / "statistical_results.json"

def test_schema_exists(schema_path):
    """Test that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_results_file_exists(results_path):
    """Test that the results file exists."""
    assert results_path.exists(), f"Results file not found at {results_path}"

def test_results_valid_against_schema(schema_path, results_path):
    """Test that the statistical results JSON conforms to the schema."""
    schema = load_schema(schema_path)
    results = load_json(results_path)
    
    # Validate the JSON against the schema
    try:
        validate(instance=results, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Results JSON does not conform to schema: {e.message}")

def test_required_fields_present(results_path):
    """Test that all required top-level fields are present."""
    results = load_json(results_path)
    required_fields = [
        "analysis_metadata",
        "model_fit",
        "hypothesis_testing",
        "coefficients",
        "p_values",
        "effect_sizes",
        "conclusion"
    ]
    
    for field in required_fields:
        assert field in results, f"Required field '{field}' missing from results"

def test_model_fit_converged_is_boolean(results_path):
    """Test that model_fit.converged is a boolean."""
    results = load_json(results_path)
    assert isinstance(results["model_fit"]["converged"], bool), \
        "model_fit.converged must be a boolean"

def test_p_values_in_range(results_path):
    """Test that all p-values are between 0 and 1."""
    results = load_json(results_path)
    p_values = results["p_values"]
    
    for key, value in p_values.items():
        assert 0 <= value <= 1, f"P-value for {key} ({value}) must be between 0 and 1"

def test_interaction_p_value_present(results_path):
    """Test that the interaction p-value is present and in range."""
    results = load_json(results_path)
    interaction_p = results["hypothesis_testing"]["interaction_p_value"]
    assert 0 <= interaction_p <= 1, "Interaction p-value must be between 0 and 1"

def test_conclusion_has_interpretation(results_path):
    """Test that the conclusion includes an interpretation string."""
    results = load_json(results_path)
    assert "interpretation" in results["conclusion"], \
        "Conclusion must include an interpretation"
    assert isinstance(results["conclusion"]["interpretation"], str), \
        "Conclusion interpretation must be a string"
    assert len(results["conclusion"]["interpretation"]) > 0, \
        "Conclusion interpretation must not be empty"