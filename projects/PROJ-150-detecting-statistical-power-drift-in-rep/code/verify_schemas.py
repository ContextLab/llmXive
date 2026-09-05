import json
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define expected schemas based on task outputs
SCHEMAS = {
    "data/derived/schema_validation.json": {
        "required_keys": ["status", "columns_found"],
        "optional_keys": ["missing_columns", "valid_levels"],
        "status_values": ["valid", "invalid"]
    },
    "data/derived/grouping_validation.json": {
        "required_keys": ["field", "original_study_id"],
        "structure": {
            "field": {"status": str, "valid_levels": list},
            "original_study_id": {"status": str, "valid_levels": list}
        }
    },
    "results/lmm_final_summary.json": {
        "required_keys": [
            "slope_year", "se_year", "ci_lower", "ci_upper",
            "p_value_lrt", "chi2_statistic", "df_diff", "methodology_note"
        ],
        "numeric_keys": ["slope_year", "se_year", "ci_lower", "ci_upper", "p_value_lrt", "chi2_statistic", "df_diff"]
    },
    "results/permutation_pvalue.json": {
        "required_keys": ["observed_slope", "empirical_p_value", "iterations", "fallback_used"],
        "numeric_keys": ["observed_slope", "empirical_p_value", "iterations"]
    },
    "results/input_permutation.json": {
        "required_keys": ["observed_slope", "null_distribution", "null_distribution_mean", "null_distribution_std", "p_value_input_perm", "iterations", "fallback_used"],
        "list_keys": ["null_distribution"],
        "numeric_keys": ["observed_slope", "null_distribution_mean", "null_distribution_std", "p_value_input_perm", "iterations"]
    },
    "results/sensitivity_report.json": {
        "required_keys": ["results"],
        "structure": {
            "results": list
        }
    },
    "results/aggregated_drift.json": {
        "required_keys": [
            "field_slopes", "heterogeneity_q", "tau_squared",
            "aggregated_slope", "aggregated_se", "aggregated_p_value"
        ],
        "numeric_keys": ["heterogeneity_q", "tau_squared", "aggregated_slope", "aggregated_se", "aggregated_p_value"]
    }
}

def verify_file_schema(file_path, schema):
    if not os.path.exists(file_path):
        logger.error(f"File missing: {file_path}")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False

    # Check required keys
    missing_keys = [k for k in schema.get("required_keys", []) if k not in data]
    if missing_keys:
        logger.error(f"{file_path}: Missing required keys: {missing_keys}")
        return False

    # Check numeric types
    for key in schema.get("numeric_keys", []):
        if key in data and not isinstance(data[key], (int, float)):
            logger.error(f"{file_path}: Key '{key}' is not numeric (got {type(data[key])})")
            return False

    # Check list types
    for key in schema.get("list_keys", []):
        if key in data and not isinstance(data[key], list):
            logger.error(f"{file_path}: Key '{key}' is not a list (got {type(data[key])})")
            return False

    # Check specific structure if defined
    if "structure" in schema:
        for key, expected_type in schema["structure"].items():
            if key in data:
                if isinstance(expected_type, dict):
                    # Nested structure check
                    for sub_key, sub_type in expected_type.items():
                        if sub_key in data[key]:
                            if not isinstance(data[key][sub_key], sub_type):
                                logger.error(f"{file_path}: Key '{key}.{sub_key}' has wrong type (expected {sub_type.__name__}, got {type(data[key][sub_key]).__name__})")
                                return False
                else:
                    if not isinstance(data[key], expected_type):
                        logger.error(f"{file_path}: Key '{key}' has wrong type (expected {expected_type.__name__}, got {type(data[key]).__name__})")
                        return False

    # Check status values
    if "status_values" in schema and "status" in data:
        if data["status"] not in schema["status_values"]:
            logger.error(f"{file_path}: Invalid status value '{data['status']}'. Expected one of {schema['status_values']}")
            return False

    logger.info(f"Schema validation passed for: {file_path}")
    return True

def main():
    all_valid = True
    for file_path, schema in SCHEMAS.items():
        if not verify_file_schema(file_path, schema):
            all_valid = False

    if all_valid:
        logger.info("All JSON artifacts verified successfully against schemas.")
        sys.exit(0)
    else:
        logger.error("Schema verification failed for one or more artifacts.")
        sys.exit(1)

if __name__ == "__main__":
    main()
