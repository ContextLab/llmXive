"""
Script to execute T050: Validate descriptors, model results, and analysis summary against schemas.
"""
import os
import sys
import logging

from code.logging_config import setup_logging
from code.validators import validate_file

def main():
    """Run validation for T050."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data", "processed")
    contracts_dir = os.path.join(base_dir, "contracts")

    files_to_validate = [
        ("descriptors.csv", "descriptor_schema.yaml"),
        ("model_results.json", "model_results_schema.yaml"),
        ("analysis_summary.json", "model_results_schema.yaml"), # Using model_results schema as placeholder for summary if no specific one exists, or adjust if specific schema exists
    ]

    all_success = True

    for data_file, schema_file in files_to_validate:
        data_path = os.path.join(data_dir, data_file)
        schema_path = os.path.join(contracts_dir, schema_file)

        logger.info(f"Validating {data_file} against {schema_file}...")

        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}")
            all_success = False
            continue

        if not os.path.exists(schema_path):
            logger.error(f"Schema file not found: {schema_path}")
            all_success = False
            continue

        success = validate_file(data_path, schema_path)
        if not success:
            logger.error(f"Validation failed for {data_file}")
            all_success = False
        else:
            logger.info(f"Validation passed for {data_file}")

    if all_success:
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("One or more validations failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()