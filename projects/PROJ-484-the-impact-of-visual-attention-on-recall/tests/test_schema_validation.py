import json
import yaml
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from validate_schemas import (
    load_schema, 
    validate_json_against_schema, 
    validate_model_output_file
)

@pytest.fixture
def schema_path():
    return Path(__file__).parent.parent / "specs" / "001-visual-attention-recall" / "contracts" / "model_output.schema.yaml"

@pytest.fixture
def valid_model_results():
    return {
        "model_formula": "recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)",
        "convergence_status": "OK",
        "fixed_effects": {
            "coefficients": {
                "Intercept": -0.5,
                "fixation_duration": 0.2,
                "valence": 0.3,
                "trait_anxiety": 0.1,
                "fixation_duration:valence": 0.05
            },
            "standard_errors": {
                "Intercept": 0.1,
                "fixation_duration": 0.05,
                "valence": 0.06,
                "trait_anxiety": 0.04,
                "fixation_duration:valence": 0.02
            },
            "z_values": {
                "Intercept": -5.0,
                "fixation_duration": 4.0,
                "valence": 5.0,
                "trait_anxiety": 2.5,
                "fixation_duration:valence": 2.5
            },
            "p_values": {
                "Intercept": 0.0001,
                "fixation_duration": 0.0001,
                "valence": 0.0001,
                "trait_anxiety": 0.01,
                "fixation_duration:valence": 0.01
            }
        },
        "random_effects": {
            "participant_variance": 0.5,
            "stimulus_variance": 0.3,
            "residual_variance": 0.2
        },
        "likelihood_ratio_test": {
            "chi_square": 10.5,
            "df": 3,
            "p_value": 0.015,
            "significant_at_alpha": True
        },
        "diagnostics": {
            "overdispersion_factor": 1.1,
            "overdispersion_status": "OK"
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00Z",
            "sample_size": 1000,
            "n_participants": 50,
            "n_stimuli": 100,
            "n_trials": 1000
        }
    }

@pytest.fixture
def valid_power_analysis():
    return {
        "simulation_parameters": {
            "n_iterations": 1000,
            "alpha_level": 0.05,
            "true_effect_size": 0.5,
            "variance_components": {
                "participant_variance": 0.5,
                "stimulus_variance": 0.3,
                "residual_variance": 0.2
            }
        },
        "results": {
            "achieved_power": 0.85,
            "confidence_interval": {
                "lower": 0.82,
                "upper": 0.88,
                "level": 0.95
            },
            "convergence_rate": 0.98
        },
        "conclusion": {
            "sufficient_power": True,
            "recommended_sample_size": 1000
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00Z",
            "seed": 42
        }
    }

@pytest.fixture
def complete_valid_output(valid_model_results, valid_power_analysis):
    return {
        "model_results": valid_model_results,
        "power_analysis": valid_power_analysis
    }

def test_load_schema(schema_path):
    """Test that the schema can be loaded successfully."""
    schema = load_schema(schema_path)
    assert schema is not None
    assert "definitions" in schema
    assert "model_results" in schema["definitions"]
    assert "power_analysis" in schema["definitions"]

def test_validate_model_results_schema(schema_path, valid_model_results):
    """Test that valid model results pass validation."""
    schema = load_schema(schema_path)
    assert validate_json_against_schema(valid_model_results, schema["definitions"]["model_results"])

def test_validate_power_analysis_schema(schema_path, valid_power_analysis):
    """Test that valid power analysis passes validation."""
    schema = load_schema(schema_path)
    assert validate_json_against_schema(valid_power_analysis, schema["definitions"]["power_analysis"])

def test_validate_complete_output(schema_path, complete_valid_output):
    """Test that the complete output file structure is valid."""
    schema = load_schema(schema_path)
    assert validate_json_against_schema(complete_valid_output, schema)

def test_validate_model_output_file(tmp_path, schema_path, complete_valid_output):
    """Test the full file validation workflow."""
    output_file = tmp_path / "model_results.json"
    with open(output_file, 'w') as f:
        json.dump(complete_valid_output, f)
    
    # This should not raise an exception
    validate_model_output_file(output_file, schema_path)

def test_invalid_convergence_status(schema_path, valid_model_results):
    """Test that invalid convergence status fails validation."""
    invalid_results = valid_model_results.copy()
    invalid_results["convergence_status"] = "INVALID_STATUS"
    
    schema = load_schema(schema_path)
    assert not validate_json_against_schema(invalid_results, schema["definitions"]["model_results"])

def test_missing_required_field(schema_path, valid_model_results):
    """Test that missing required fields fail validation."""
    invalid_results = valid_model_results.copy()
    del invalid_results["fixed_effects"]
    
    schema = load_schema(schema_path)
    assert not validate_json_against_schema(invalid_results, schema["definitions"]["model_results"])

def test_invalid_p_value_range(schema_path, valid_model_results):
    """Test that p-values outside [0, 1] fail validation."""
    invalid_results = valid_model_results.copy()
    invalid_results["fixed_effects"]["p_values"]["Intercept"] = 1.5
    
    schema = load_schema(schema_path)
    assert not validate_json_against_schema(invalid_results, schema["definitions"]["model_results"])