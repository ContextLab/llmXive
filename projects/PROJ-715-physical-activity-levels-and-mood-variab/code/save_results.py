import os
import sys
import logging
import json
from pathlib import Path

from analysis import run_analysis
from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema definition."""
    import yaml
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_results_schema(results: dict, schema: dict) -> bool:
    """
    Validate the results dictionary against the JSON schema definition.
    Performs basic structural checks based on the schema keys.
    """
    required_keys = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required top-level keys
    for key in required_keys:
        if key not in results:
            logger.error(f"Validation failed: Missing required key '{key}'")
            return False

    # Check types of specific known fields if defined in schema
    if "properties" in schema:
        for key, prop_def in properties.items():
            if key in results:
                expected_type = prop_def.get("type")
                if expected_type == "object" and not isinstance(results[key], dict):
                    logger.error(f"Validation failed: '{key}' should be an object")
                    return False
                if expected_type == "array" and not isinstance(results[key], list):
                    logger.error(f"Validation failed: '{key}' should be an array")
                    return False
                if expected_type == "string" and not isinstance(results[key], str):
                    logger.error(f"Validation failed: '{key}' should be a string")
                    return False
                if expected_type == "number" and not isinstance(results[key], (int, float)):
                    logger.error(f"Validation failed: '{key}' should be a number")
                    return False

    logger.info("Schema validation passed.")
    return True


def save_results_to_json(results: dict, output_path: Path) -> None:
    """Save the results dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")


def main():
    """
    Main entry point for T025: Save model results to JSON and validate.
    1. Runs the analysis pipeline (T019-T024) to get results.
    2. Loads the schema from specs.
    3. Validates the results.
    4. Saves to data/processed/model_results.json.
    """
    logger.info("Starting T025: Save and validate model results.")

    # 1. Run analysis to get results
    # The run_analysis function (implemented in T019-T024) returns the results dict
    try:
        results = run_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    if not results:
        logger.error("Analysis returned empty results.")
        sys.exit(1)

    # 2. Load schema
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    schema = load_schema(schema_path)

    # 3. Validate results
    if not validate_results_schema(results, schema):
        logger.error("Results validation failed. Aborting save.")
        sys.exit(1)

    # 4. Save results
    output_path = get_path("data/processed/model_results.json")
    save_results_to_json(results, output_path)

    logger.info("T025 completed successfully.")


if __name__ == "__main__":
    main()
