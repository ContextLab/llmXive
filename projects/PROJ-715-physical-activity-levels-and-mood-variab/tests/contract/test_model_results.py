"""
Contract test for model_results.json schema.
Validates the structure and required fields of the model results output.
"""
import json
import os
import pytest
from pathlib import Path

# Import schema loading utility from the project's output_validator module
# Note: We need to add the code directory to the path to import it
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from output_validator import load_schema, validate_dataframe

# Import config to get paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from config import get_path


def test_model_results_schema_exists():
    """Test that the model_results schema file exists."""
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")
    assert schema_path.exists(), f"Schema file not found at {schema_path}"


def test_model_results_json_exists():
    """Test that model_results.json exists (will fail if analysis hasn't run yet)."""
    output_path = get_path("data/processed/model_results.json")
    assert output_path.exists(), f"Model results file not found at {output_path}. " \
                                "Run code/analysis.py to generate the file."


def test_model_results_schema_validation():
    """
    Contract test: Validate model_results.json against model_results.schema.yaml.
    This test ensures the output structure matches the specification.
    """
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")
    output_path = get_path("data/processed/model_results.json")

    # Load schema
    schema = load_schema(schema_path)

    # Load JSON data
    with open(output_path, 'r') as f:
        data = json.load(f)

    # Basic structure validation
    assert isinstance(data, dict), "Root element must be a dictionary"

    # Check for required top-level keys
    required_keys = ["models", "metadata", "diagnostics"]
    for key in required_keys:
        assert key in data, f"Missing required top-level key: {key}"

    # Validate models section
    assert isinstance(data["models"], dict), "models must be a dictionary"
    assert "variability_model" in data["models"], "Missing 'variability_model' in models"
    assert "mean_mood_model" in data["models"], "Missing 'mean_mood_model' in models"

    # Validate variability_model structure
    variability = data["models"]["variability_model"]
    assert "outcome" in variability, "variability_model missing 'outcome'"
    assert "predictor" in variability, "variability_model missing 'predictor'"
    assert "fixed_effects" in variability, "variability_model missing 'fixed_effects'"
    assert "random_effects" in variability, "variability_model missing 'random_effects'"
    assert "converged" in variability, "variability_model missing 'converged'"
    assert variability["outcome"] == "log_mood_std", "Unexpected outcome for variability model"
    assert variability["predictor"] == "total_steps", "Unexpected predictor for variability model"

    # Validate mean_mood_model structure
    mean_mood = data["models"]["mean_mood_model"]
    assert "outcome" in mean_mood, "mean_mood_model missing 'outcome'"
    assert "predictor" in mean_mood, "mean_mood_model missing 'predictor'"
    assert "fixed_effects" in mean_mood, "mean_mood_model missing 'fixed_effects'"
    assert "random_effects" in mean_mood, "mean_mood_model missing 'random_effects'"
    assert "converged" in mean_mood, "mean_mood_model missing 'converged'"
    assert mean_mood["outcome"] == "mean_mood", "Unexpected outcome for mean_mood model"
    assert mean_mood["predictor"] == "total_steps", "Unexpected predictor for mean_mood model"

    # Validate fixed_effects structure for both models
    for model_name, model_data in [("variability_model", variability), ("mean_mood_model", mean_mood)]:
        fe = model_data["fixed_effects"]
        assert isinstance(fe, list), f"{model_name}: fixed_effects must be a list"
        assert len(fe) > 0, f"{model_name}: fixed_effects is empty"

        for effect in fe:
            assert "term" in effect, f"{model_name}: fixed effect missing 'term'"
            assert "estimate" in effect, f"{model_name}: fixed effect missing 'estimate'"
            assert "std_error" in effect, f"{model_name}: fixed effect missing 'std_error'"
            assert "p_value" in effect, f"{model_name}: fixed effect missing 'p_value'"
            assert "ci_lower" in effect, f"{model_name}: fixed effect missing 'ci_lower'"
            assert "ci_upper" in effect, f"{model_name}: fixed effect missing 'ci_upper'"
            assert isinstance(effect["estimate"], (int, float)), f"{model_name}: estimate must be numeric"
            assert isinstance(effect["std_error"], (int, float)), f"{model_name}: std_error must be numeric"
            assert isinstance(effect["p_value"], (int, float)), f"{model_name}: p_value must be numeric"

    # Validate metadata section
    metadata = data["metadata"]
    assert "analysis_type" in metadata, "metadata missing 'analysis_type'"
    assert metadata["analysis_type"] == "associational", "analysis_type must be 'associational'"
    assert "n_observations" in metadata, "metadata missing 'n_observations'"
    assert "n_participants" in metadata, "metadata missing 'n_participants'"
    assert isinstance(metadata["n_observations"], int), "n_observations must be integer"
    assert isinstance(metadata["n_participants"], int), "n_participants must be integer"

    # Validate diagnostics section
    diagnostics = data["diagnostics"]
    assert "shapiro_wilk" in diagnostics, "diagnostics missing 'shapiro_wilk'"
    assert "breusch_pagan" in diagnostics, "diagnostics missing 'breusch_pagan'"
    assert "lopo_consistency" in diagnostics, "diagnostics missing 'lopo_consistency'"
    assert "sensitivity_analysis" in diagnostics, "diagnostics missing 'sensitivity_analysis'"

    # Validate LOPO consistency structure
    lopo = diagnostics["lopo_consistency"]
    assert "sign_stability_pct" in lopo, "lopo_consistency missing 'sign_stability_pct'"
    assert "threshold" in lopo, "lopo_consistency missing 'threshold'"
    assert "passed" in lopo, "lopo_consistency missing 'passed'"
    assert isinstance(lopo["sign_stability_pct"], (int, float)), "sign_stability_pct must be numeric"

    # Validate sensitivity analysis structure
    sensitivity = diagnostics["sensitivity_analysis"]
    assert "weekdays_only" in sensitivity, "sensitivity_analysis missing 'weekdays_only'"
    assert "alternative_metric" in sensitivity, "sensitivity_analysis missing 'alternative_metric'"
    assert "single_rating_handling" in sensitivity, "sensitivity_analysis missing 'single_rating_handling'"

    # Validate weekdays_only sensitivity
    weekdays = sensitivity["weekdays_only"]
    assert "coefficient" in weekdays, "weekdays_only missing 'coefficient'"
    assert "direction_consistent" in weekdays, "weekdays_only missing 'direction_consistent'"

    # Validate alternative_metric sensitivity
    alt_metric = sensitivity["alternative_metric"]
    assert "metric_name" in alt_metric, "alternative_metric missing 'metric_name'"
    assert "direction_consistent" in alt_metric, "alternative_metric missing 'direction_consistent'"

    # Validate single_rating_handling sensitivity
    single_rating = sensitivity["single_rating_handling"]
    assert "exclusion_model" in single_rating, "single_rating_handling missing 'exclusion_model'"
    assert "imputation_model" in single_rating, "single_rating_handling missing 'imputation_model'"
    assert "bootstrap_consistency_pct" in single_rating, "single_rating_handling missing 'bootstrap_consistency_pct'"

    # Validate bootstrap consistency
    assert isinstance(single_rating["bootstrap_consistency_pct"], (int, float)), \
        "bootstrap_consistency_pct must be numeric"
    assert single_rating["bootstrap_consistency_pct"] >= 80.0, \
        f"Bootstrap consistency ({single_rating['bootstrap_consistency_pct']}%) is below 80% threshold"

    # Validate that all models converged
    assert variability["converged"], "variability_model did not converge"
    assert mean_mood["converged"], "mean_mood_model did not converge"

    # Validate LOPO threshold
    assert lopo["threshold"] == 90.0, "LOPO threshold should be 90%"
    assert lopo["sign_stability_pct"] >= lopo["threshold"], \
        f"LOPO sign stability ({lopo['sign_stability_pct']}%) is below threshold ({lopo['threshold']}%)"

def test_schema_yaml_syntax():
    """Test that the schema YAML file is valid YAML."""
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        assert schema is not None, "Schema file is empty or invalid YAML"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema file: {e}")

def test_json_valid_format():
    """Test that model_results.json is valid JSON."""
    output_path = get_path("data/processed/model_results.json")
    
    try:
        with open(output_path, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in model_results.json: {e}")

def test_required_covariates_present():
    """Test that required covariates are present in fixed effects."""
    output_path = get_path("data/processed/model_results.json")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    required_covariates = ["sleep_duration", "day_of_week", "baseline_affect"]
    
    for model_name in ["variability_model", "mean_mood_model"]:
        fixed_effects = data["models"][model_name]["fixed_effects"]
        effect_terms = [ef["term"] for ef in fixed_effects]
        
        for covariate in required_covariates:
            assert covariate in effect_terms, \
                f"{model_name} missing required covariate: {covariate}"

def test_p_values_in_valid_range():
    """Test that all p-values are in valid range [0, 1]."""
    output_path = get_path("data/processed/model_results.json")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    for model_name in ["variability_model", "mean_mood_model"]:
        fixed_effects = data["models"][model_name]["fixed_effects"]
        
        for effect in fixed_effects:
            p_val = effect["p_value"]
            assert 0 <= p_val <= 1, \
                f"Invalid p-value {p_val} for term {effect['term']} in {model_name}"

def test_confidence_intervals_valid():
    """Test that confidence intervals are logically valid (lower < upper)."""
    output_path = get_path("data/processed/model_results.json")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    for model_name in ["variability_model", "mean_mood_model"]:
        fixed_effects = data["models"][model_name]["fixed_effects"]
        
        for effect in fixed_effects:
            ci_lower = effect["ci_lower"]
            ci_upper = effect["ci_upper"]
            assert ci_lower <= ci_upper, \
                f"Invalid CI [{ci_lower}, {ci_upper}] for term {effect['term']} in {model_name}"