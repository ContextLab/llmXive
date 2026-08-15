import json
import pytest
from pathlib import Path
import yaml
import sys
import os

# Add code directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_path
from output_validator import load_schema

def load_sample_results():
    """Load a sample results structure for testing purposes."""
    # This mimics the structure expected from analysis.py
    return {
        "models": [
            {
                "model_name": "mood_std_model",
                "outcome": "log_mood_std",
                "predictor": "total_steps",
                "fixed_effects": {
                    "total_steps": {"estimate": 0.05, "se": 0.02, "p_value": 0.01, "ci_lower": 0.01, "ci_upper": 0.09}
                },
                "converged": True
            },
            {
                "model_name": "mean_mood_model",
                "outcome": "mean_mood",
                "predictor": "total_steps",
                "fixed_effects": {
                    "total_steps": {"estimate": 0.001, "se": 0.0005, "p_value": 0.03, "ci_lower": 0.0001, "ci_upper": 0.0019}
                },
                "converged": True
            }
        ],
        "diagnostics": {
            "shapiro_wilk": {"statistic": 0.98, "p_value": 0.15},
            "breusch_pagan": {"statistic": 1.2, "p_value": 0.25}
        },
        "lopo_results": {
            "sign_stability": 0.95,
            "folds": 10
        },
        "sensitivity_analysis": {
            "weekdays_only": {"coefficient": 0.048},
            "active_minutes": {"coefficient": 0.045}
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00",
            "pipeline_version": "1.0.0"
        }
    }

@pytest.fixture
def schema_path():
    return get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")

@pytest.fixture
def results_data():
    return load_sample_results()

def test_schema_exists(schema_path):
    """Verify the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_schema_is_valid_yaml(schema_path):
    """Verify the schema file is valid YAML."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema: {e}")

def test_results_structure_matches_schema(results_data, schema_path):
    """Contract test: Ensure the results structure matches the schema definition."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic contract checks derived from the schema structure
    assert "models" in results_data, "Missing 'models' key"
    assert isinstance(results_data["models"], list), "'models' must be a list"
    assert len(results_data["models"]) >= 2, "Must have at least two models"
    
    for model in results_data["models"]:
        assert "model_name" in model, "Model missing 'model_name'"
        assert "fixed_effects" in model, "Model missing 'fixed_effects'"
        assert "converged" in model, "Model missing 'converged' status"
        
        # Check fixed effects structure
        for var, stats in model["fixed_effects"].items():
            assert "estimate" in stats, f"Missing 'estimate' for {var}"
            assert "p_value" in stats, f"Missing 'p_value' for {var}"

def test_save_results_contract(tmp_path, results_data, schema_path):
    """Contract test: Verify the save_results script produces valid JSON matching schema."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from save_results import save_results_to_json, validate_results_schema
    
    output_file = tmp_path / "model_results.json"
    
    # Save
    save_results_to_json(results_data, output_file)
    
    # Verify file exists
    assert output_file.exists(), "Output JSON file was not created"
    
    # Verify content is valid JSON
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == results_data, "Saved JSON does not match input data"
    
    # Verify against schema
    validate_results_schema(loaded, schema_path)
