"""
Execution script for T050: Validation of processed artifacts against schemas.
Runs the validators.py CLI to check descriptors.csv, model_results.json, and analysis_summary.json.
"""
import os
import sys
import logging
from code.logging_config import setup_logging
from code.validators import validate_file

# Setup logging
logger = setup_logging(__name__)

def main():
    """Run validation for all key artifacts."""
    # Define artifacts and their schemas
    validations = [
        ('data/processed/descriptors.csv', 'contracts/descriptor_schema.yaml'),
        ('data/processed/model_results.json', 'contracts/model_results_schema.yaml'),
        ('data/processed/analysis_summary.json', 'contracts/model_results_schema.yaml'), # Using model_results schema for analysis_summary as per task description logic
    ]

    all_passed = True

    for data_file, schema_file in validations:
        if not os.path.exists(data_file):
            logger.error(f"Artifact missing: {data_file}")
            all_passed = False
            continue

        if not os.path.exists(schema_file):
            logger.error(f"Schema missing: {schema_file}")
            all_passed = False
            continue

        logger.info(f"Validating {data_file} against {schema_file}...")
        if validate_file(data_file, schema_file):
            logger.info(f"PASS: {data_file}")
        else:
            logger.error(f"FAIL: {data_file}")
            all_passed = False

    if all_passed:
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("One or more validations failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
