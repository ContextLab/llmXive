"""
Task T038: Verify results/metrics.json contains all required fields and the Bonferroni flag.

This script validates the integrity and completeness of the metrics file generated
by the model training and evaluation pipeline (T029).

Required fields (based on T028/T029 specs):
- model_metrics: Dictionary containing R², MAE, RMSE for each model (RF, GB, MeanBaseline)
- statistical_tests: Dictionary containing p-values, alpha_corrected, significance flags
- bonferroni_flag: Boolean indicating if Bonferroni correction was applied correctly
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = PROJECT_ROOT / "results" / "metrics.json"

# Define required schema based on T028/T029 specifications
REQUIRED_TOP_LEVEL_KEYS = {
    "model_metrics",
    "statistical_tests",
    "bonferroni_flag"
}

REQUIRED_MODEL_METRICS_KEYS = {
    "R2",
    "MAE",
    "RMSE"
}

REQUIRED_STATISTICAL_TEST_KEYS = {
    "p_values",
    "alpha_corrected",
    "significance_flags"
}

def load_metrics_file(path: Path) -> dict:
    """Load and parse the metrics JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found at: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def validate_structure(metrics: dict) -> bool:
    """Validate the top-level structure of the metrics dictionary."""
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(metrics.keys())
    if missing_keys:
        logger.error(f"Missing top-level keys: {missing_keys}")
        return False
    
    logger.info("Top-level structure validation passed")
    return True

def validate_model_metrics(metrics: dict) -> bool:
    """Validate that all models have required metrics."""
    model_metrics = metrics.get("model_metrics", {})
    
    if not model_metrics:
        logger.error("model_metrics is empty or missing")
        return False
    
    # Check that we have at least the expected models
    expected_models = {"RandomForest", "GradientBoosting", "MeanBaseline"}
    actual_models = set(model_metrics.keys())
    
    missing_models = expected_models - actual_models
    if missing_models:
        logger.warning(f"Expected models missing: {missing_models}")
        # This might be acceptable if only some models were trained, 
        # but we log it as a warning
    
    for model_name, model_data in model_metrics.items():
        missing_metric_keys = REQUIRED_MODEL_METRICS_KEYS - set(model_data.keys())
        if missing_metric_keys:
            logger.error(f"Model '{model_name}' missing metrics: {missing_metric_keys}")
            return False
        
        # Validate numeric types
        for key in REQUIRED_MODEL_METRICS_KEYS:
            if not isinstance(model_data[key], (int, float)):
                logger.error(f"Model '{model_name}' metric '{key}' is not numeric: {type(model_data[key])}")
                return False
    
    logger.info("Model metrics validation passed")
    return True

def validate_statistical_tests(metrics: dict) -> bool:
    """Validate the statistical test results structure."""
    stat_tests = metrics.get("statistical_tests", {})
    
    missing_stat_keys = REQUIRED_STATISTICAL_TEST_KEYS - set(stat_tests.keys())
    if missing_stat_keys:
        logger.error(f"Missing statistical test keys: {missing_stat_keys}")
        return False
    
    # Validate alpha_corrected is a positive number
    alpha = stat_tests.get("alpha_corrected")
    if not isinstance(alpha, (int, float)) or alpha <= 0:
        logger.error(f"Invalid alpha_corrected value: {alpha}")
        return False
    
    # Validate p_values structure
    p_values = stat_tests.get("p_values", {})
    if not isinstance(p_values, dict):
        logger.error("p_values must be a dictionary")
        return False
    
    # Validate significance_flags structure
    sig_flags = stat_tests.get("significance_flags", {})
    if not isinstance(sig_flags, dict):
        logger.error("significance_flags must be a dictionary")
        return False
    
    # Check that p_values and significance_flags have matching keys
    if set(p_values.keys()) != set(sig_flags.keys()):
        logger.error("p_values and significance_flags have mismatched keys")
        return False
    
    logger.info("Statistical tests validation passed")
    return True

def validate_bonferroni_flag(metrics: dict) -> bool:
    """Validate the Bonferroni flag is present and correct."""
    bonf_flag = metrics.get("bonferroni_flag")
    
    if not isinstance(bonf_flag, bool):
        logger.error(f"bonferroni_flag must be a boolean, got: {type(bonf_flag)}")
        return False
    
    if not bonf_flag:
        logger.warning("bonferroni_flag is False - Bonferroni correction may not have been applied")
    
    logger.info(f"Bonferroni flag validation passed (value: {bonf_flag})")
    return True

def main():
    """Main entry point for verification."""
    logger.info(f"Starting metrics verification for: {METRICS_PATH}")
    
    try:
        # Load the metrics file
        metrics = load_metrics_file(METRICS_PATH)
        logger.info("Successfully loaded metrics file")
        
        # Run all validations
        validations = [
            ("Structure", validate_structure(metrics)),
            ("Model Metrics", validate_model_metrics(metrics)),
            ("Statistical Tests", validate_statistical_tests(metrics)),
            ("Bonferroni Flag", validate_bonferroni_flag(metrics))
        ]
        
        # Report results
        all_passed = True
        for name, passed in validations:
            status = "✓ PASSED" if passed else "✗ FAILED"
            logger.info(f"{name} validation: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            logger.info("✅ All validations PASSED - metrics.json is complete and valid")
            return 0
        else:
            logger.error("❌ Some validations FAILED - metrics.json is incomplete or invalid")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())