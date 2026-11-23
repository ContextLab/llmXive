import pytest
import json
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from config import get_path

def load_schema():
    """Load the model_results schema from the contracts directory."""
    schema_path = get_path('specs', '001-physical-activity-levels-and-mood-variab', 'contracts', 'model_results.schema.yaml')
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(data, schema):
    """
    Basic validation of data against the schema structure.
    Checks for required top-level keys and basic types.
    """
    required_keys = schema.get('required', [])
    for key in required_keys:
        if key not in data:
            raise AssertionError(f"Missing required key in model_results.json: '{key}'")
    
    # Specific type checks for complex structures
    if 'fixed_effects' in data:
        assert isinstance(data['fixed_effects'], dict), "fixed_effects must be a dictionary"
    
    if 'random_effects' in data:
        assert isinstance(data['random_effects'], dict), "random_effects must be a dictionary"
    
    if 'model_fit' in data:
        assert isinstance(data['model_fit'], dict), "model_fit must be a dictionary"
    
    if 'diagnostic_tests' in data:
        assert isinstance(data['diagnostic_tests'], dict), "diagnostic_tests must be a dictionary"
    
    if 'validation' in data:
        assert isinstance(data['validation'], dict), "validation must be a dictionary"
    
    if 'sensitivity' in data:
        assert isinstance(data['sensitivity'], dict), "sensitivity must be a dictionary"

def test_model_results_schema():
    """
    Contract test: Verify that model_results.json exists and conforms to the 
    model_results.schema.yaml definition.
    """
    path = get_path('data/processed/model_results.json')
    
    # Skip if file doesn't exist (analysis hasn't run yet)
    if not path.exists():
        pytest.skip("model_results.json not found. Run analysis pipeline first.")
    
    # Load the JSON data
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Load the schema
    schema = load_schema()
    
    # Validate structure
    validate_against_schema(data, schema)
    
    # Additional specific checks based on the schema definition
    # Check fixed_effects structure (keys should be predictor names)
    if 'fixed_effects' in data:
        for predictor, stats in data['fixed_effects'].items():
            assert isinstance(stats, dict), f"Stats for {predictor} must be a dict"
            required_stats = ['estimate', 'std_err', 'p_value']
            for stat in required_stats:
                assert stat in stats, f"Missing '{stat}' in fixed_effects.{predictor}"
    
    # Check diagnostic_tests
    if 'diagnostic_tests' in data:
        assert 'shapiro_wilk_p_value' in data['diagnostic_tests'], "Missing shapiro_wilk_p_value"
        assert 'breusch_pagan_p_value' in data['diagnostic_tests'], "Missing breusch_pagan_p_value"
    
    # Check validation metrics
    if 'validation' in data:
        assert 'lopo_average_rmse' in data['validation'], "Missing lopo_average_rmse"
        assert 'lopo_sign_consistency_pct' in data['validation'], "Missing lopo_sign_consistency_pct"
    
    # Check sensitivity analysis
    if 'sensitivity' in data:
        assert 'single_rating_bootstrap_pass' in data['sensitivity'], "Missing single_rating_bootstrap_pass"