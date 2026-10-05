"""
Contract schema validators for the statistical analysis pipeline.

This module defines and validates the schema for data artifacts generated
by the pipeline, ensuring consistency and correctness per Constitution Principle V.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_project_root, get_data_dir, get_artifacts_dir
from logging_config import get_logger

logger = get_logger(__name__)

# Schema Definitions
# These schemas define the expected structure of output files.
# They are used to validate that data ingestion and processing steps
# produce artifacts in the correct format.

SCHEMA_B_SPLINE_COEFFICIENTS = {
    "type": "object",
    "required": ["metadata", "coefficients"],
    "properties": {
        "metadata": {
            "type": "object",
            "required": ["model_id", "variable", "timestamp", "basis_dimension"],
            "properties": {
                "model_id": {"type": "string"},
                "variable": {"type": "string"},
                "timestamp": {"type": "string"},
                "basis_dimension": {"type": "integer", "minimum": 1},
                "imputation_flags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "coefficients": {
            "type": "array",
            "items": {
                "type": "number"
            }
        }
    }
}

SCHEMA_FPCA_RESULTS = {
    "type": "object",
    "required": ["eigenvalues", "eigenfunctions", "cumulative_variance", "metadata"],
    "properties": {
        "eigenvalues": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 1
        },
        "eigenfunctions": {
            "type": "array",
            "items": {"type": "array"}
        },
        "cumulative_variance": {
            "type": "array",
            "items": {"type": "number", "minimum": 0.0, "maximum": 1.0}
        },
        "metadata": {
            "type": "object",
            "required": ["total_components", "variance_threshold"],
            "properties": {
                "total_components": {"type": "integer"},
                "variance_threshold": {"type": "number"}
            }
        }
    }
}

SCHEMA_LOO_ROBUSTNESS = {
    "type": "object",
    "required": ["stability_metrics", "unstable_modes", "metadata"],
    "properties": {
        "stability_metrics": {
            "type": "object",
            "required": ["correlations", "std_dev"],
            "properties": {
                "correlations": {
                    "type": "array",
                    "items": {"type": "number", "minimum": -1.0, "maximum": 1.0}
                },
                "std_dev": {"type": "number", "minimum": 0.0}
            }
        },
        "unstable_modes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["mode_index", "correlation"],
                "properties": {
                    "mode_index": {"type": "integer"},
                    "correlation": {"type": "number"}
                }
            }
        },
        "metadata": {
            "type": "object",
            "required": ["ensemble_size", "threshold"],
            "properties": {
                "ensemble_size": {"type": "integer"},
                "threshold": {"type": "number"}
            }
        }
    }
}

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_name: str) -> bool:
    """
    Validates a data dictionary against a JSON Schema definition.

    Args:
        data: The data to validate.
        schema: The JSON Schema definition.
        schema_name: Name of the schema for logging purposes.

    Returns:
        True if valid, raises ValueError if invalid.
    """
    # Basic type checking
    if not isinstance(data, dict):
        raise ValueError(f"Validation failed for {schema_name}: Expected dict, got {type(data)}")

    # Check required fields
    required_fields = schema.get("required", [])
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(
            f"Validation failed for {schema_name}: Missing required fields: {missing_fields}"
        )

    # Check property types
    properties = schema.get("properties", {})
    for field, spec in properties.items():
        if field in data:
            value = data[field]
            expected_type = spec.get("type")

            if expected_type == "object":
                if not isinstance(value, dict):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected object, got {type(value)}"
                    )
                # Recursively validate nested objects if nested schema exists
                if "properties" in spec:
                    # Simple recursive check for nested required fields
                    nested_required = spec.get("required", [])
                    nested_missing = [f for f in nested_required if f not in value]
                    if nested_missing:
                        raise ValueError(
                            f"Validation failed for {schema_name}.{field}: Missing nested fields: {nested_missing}"
                        )
            elif expected_type == "array":
                if not isinstance(value, list):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected array, got {type(value)}"
                    )
                if spec.get("minItems") is not None and len(value) < spec["minItems"]:
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Array too short (min {spec['minItems']})"
                    )
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected number, got {type(value)}"
                    )
            elif expected_type == "integer":
                if not isinstance(value, int):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected integer, got {type(value)}"
                    )
            elif expected_type == "string":
                if not isinstance(value, str):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected string, got {type(value)}"
                    )
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    raise ValueError(
                        f"Validation failed for {schema_name}.{field}: Expected boolean, got {type(value)}"
                    )

    logger.info(f"Schema validation passed for {schema_name}")
    return True

def validate_file_against_schema(file_path: str, schema: Dict[str, Any], schema_name: str) -> bool:
    """
    Loads a JSON file and validates it against a schema.

    Args:
        file_path: Path to the JSON file.
        schema: The JSON Schema definition.
        schema_name: Name of the schema for logging.

    Returns:
        True if valid.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for validation: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

    return validate_schema(data, schema, schema_name)

def run_contract_tests() -> None:
    """
    Runs contract tests against existing artifacts if they exist.
    This is a placeholder for when artifacts are generated.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    artifacts_dir = get_artifacts_dir()

    logger.info("Running contract schema validators...")

    # Check for B-Spline coefficients (US1)
    spline_path = data_dir / "processed" / "bspline_coefficients.json"
    if spline_path.exists():
        try:
            validate_file_against_schema(str(spline_path), SCHEMA_B_SPLINE_COEFFICIENTS, "B-Spline Coefficients")
        except ValueError as e:
            logger.error(f"Contract test failed for B-Spline Coefficients: {e}")
            raise
    else:
        logger.info("Skipping B-Spline Coefficients validation: File not found (expected before US1 completion)")

    # Check for FPCA results (US2)
    fpca_path = data_dir / "processed" / "fpca_results.json"
    if fpca_path.exists():
        try:
            validate_file_against_schema(str(fpca_path), SCHEMA_FPCA_RESULTS, "FPCA Results")
        except ValueError as e:
            logger.error(f"Contract test failed for FPCA Results: {e}")
            raise
    else:
        logger.info("Skipping FPCA Results validation: File not found (expected before US2 completion)")

    # Check for LOO Robustness results (US3)
    loo_path = artifacts_dir / "unstable_modes.json"
    if loo_path.exists():
        try:
            validate_file_against_schema(str(loo_path), SCHEMA_LOO_ROBUSTNESS, "LOO Robustness")
        except ValueError as e:
            logger.error(f"Contract test failed for LOO Robustness: {e}")
            raise
    else:
        logger.info("Skipping LOO Robustness validation: File not found (expected before US3 completion)")

    logger.info("Contract schema validators completed successfully.")

if __name__ == "__main__":
    run_contract_tests()