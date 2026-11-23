import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from save_results import validate_results_schema, save_results_to_json
from config import get_path

@pytest.fixture
def sample_results():
    """Create a minimal valid results dictionary for testing."""
    return {
        "models": {
            "mood_variability": {
                "outcome": "log(mood_std + 0.01)",
                "predictor": "total_steps",
                "fixed_effects": {
                    "total_steps": {
                        "estimate": -0.001,
                        "std_error": 0.0005,
                        "p_value": 0.04,
                        "ci_lower_95": -0.002,
                        "ci_upper_95": -0.0001
                    },
                    "sleep_duration": {"estimate": 0.5, "std_error": 0.1, "p_value": 0.01},
                    "day_of_week": {"estimate": 0.2, "std_error": 0.1, "p_value": 0.05},
                    "baseline_affect": {"estimate": 0.3, "std_error": 0.1, "p_value": 0.02}
                },
                "random_effects": {
                    "participant_intercept_variance": 0.5,
                    "residual_variance": 0.3
                },
                "convergence_status": True,
                "type": "Linear Mixed Effects Model",
                "association_type": "associational"
            },
            "mean_mood": {
                "outcome": "mean_mood",
                "predictor": "total_steps",
                "fixed_effects": {
                    "total_steps": {
                        "estimate": 0.0005,
                        "std_error": 0.0002,
                        "p_value": 0.01,
                        "ci_lower_95": 0.0001,
                        "ci_upper_95": 0.001
                    },
                    "sleep_duration": {"estimate": 0.8, "std_error": 0.1, "p_value": 0.001},
                    "day_of_week": {"estimate": 0.1, "std_error": 0.1, "p_value": 0.3},
                    "baseline_affect": {"estimate": 0.4, "std_error": 0.1, "p_value": 0.005}
                },
                "random_effects": {
                    "participant_intercept_variance": 0.4,
                    "residual_variance": 0.2
                },
                "convergence_status": True,
                "type": "Linear Mixed Effects Model",
                "association_type": "associational"
            }
        },
        "validation": {
            "lopo": {
                "sign_consistency": 0.95,
                "average_rmse": 0.12,
                "threshold_met": True
            },
            "sensitivity": {
                "weekdays_only": {
                    "coefficient_direction_match": True,
                    "coefficient_difference_pct": 5.2
                },
                "single_rating_bootstrap": {
                    "consistency_percentage": 85.0,
                    "threshold_met": True
                }
            }
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00",
            "version": "1.0.0",
            "dataset_source": "OSF StudentLife",
            "software_environment": {
                "python_version": "3.9.0",
                "pandas_version": "1.5.0",
                "statsmodels_version": "0.13.0"
            }
        }
    }

@pytest.fixture
def schema_path():
    """Return the path to the model results schema."""
    return get_path('specs', '001-physical-activity-levels-and-mood-variability', 
                   'contracts', 'model_results.schema.yaml')

def test_validate_results_schema_valid(sample_results, schema_path):
    """Test that a valid results dictionary passes validation."""
    assert validate_results_schema(sample_results, schema_path) is True

def test_validate_results_schema_missing_key(sample_results, schema_path):
    """Test that validation fails when a required key is missing."""
    invalid_results = sample_results.copy()
    del invalid_results['models']
    
    with pytest.raises(ValueError, match="Missing required key"):
        validate_results_schema(invalid_results, schema_path)

def test_validate_results_schema_invalid_model_type(sample_results, schema_path):
    """Test that validation fails if model data is not a dictionary."""
    invalid_results = sample_results.copy()
    invalid_results['models']['mood_variability'] = "string instead of dict"
    
    with pytest.raises(ValueError, match="must be a dictionary"):
        validate_results_schema(invalid_results, schema_path)

def test_save_results_to_json(tmp_path, sample_results):
    """Test that results are saved correctly to JSON."""
    output_file = tmp_path / "test_results.json"
    save_results_to_json(sample_results, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)
    
    assert loaded_data == sample_results
    assert loaded_data['metadata']['version'] == "1.0.0"

def test_save_and_validate_integration(sample_results, schema_path, tmp_path):
    """Integration test: save and then validate the saved file."""
    output_file = tmp_path / "integration_test.json"
    
    # Save
    save_results_to_json(sample_results, output_file)
    
    # Load back
    with open(output_file, 'r') as f:
        loaded_data = json.load(f)
    
    # Validate
    assert validate_results_schema(loaded_data, schema_path) is True
