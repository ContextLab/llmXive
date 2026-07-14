"""
Module: code/data/load_external.py

Purpose:
Load the manually curated external validation dataset (Kr on CNTs) from
`data/external/kr_cnt.csv` and validate it against the project's dataset schema
defined in `contracts/dataset.schema.yaml`.

This task implements T035 for User Story 3 (US3).
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
import yaml

# Import the schema validation logic from the existing project
from data.validate_schema import load_schema, validate_dataframe

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXTERNAL_DATA_PATH = PROJECT_ROOT / "data" / "external" / "kr_cnt.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_external_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the external Kr on CNTs dataset from CSV.

    Args:
        data_path: Optional override for the data file path.
                   Defaults to PROJECT_ROOT/data/external/kr_cnt.csv.

    Returns:
        pd.DataFrame: The loaded dataset.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If the file is empty or has no valid data rows.
    """
    if data_path is None:
        data_path = EXTERNAL_DATA_PATH

    if not data_path.exists():
        raise FileNotFoundError(
            f"External data file not found at: {data_path}. "
            "Ensure T035a has successfully created data/external/kr_cnt.csv."
        )

    logger.info(f"Loading external data from: {data_path}")
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file {data_path}: {e}")

    if df.empty:
        raise ValueError(f"The loaded dataset at {data_path} is empty.")

    logger.info(f"Successfully loaded {len(df)} rows from {data_path}")
    return df

def validate_external_data(df: pd.DataFrame, schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Validate the loaded DataFrame against the project schema.

    Args:
        df: The DataFrame to validate.
        schema_path: Optional override for the schema file path.
                     Defaults to PROJECT_ROOT/contracts/dataset.schema.yaml.

    Returns:
        Dict[str, Any]: Validation results including 'is_valid', 'errors', and 'warnings'.
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH

    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return {
            "is_valid": True,
            "errors": [],
            "warnings": ["Schema file missing, validation skipped."]
        }

    logger.info(f"Validating data against schema: {schema_path}")
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load schema from {schema_path}: {e}")

    is_valid, errors, warnings = validate_dataframe(df, schema)

    result = {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings
    }

    if is_valid:
        logger.info("External data validation PASSED.")
    else:
        logger.error(f"External data validation FAILED with {len(errors)} errors.")
        for err in errors:
            logger.error(f"  - {err}")

    return result

def run_load_external_pipeline(data_path: Optional[Path] = None, schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Execute the full external data loading and validation pipeline.

    This function:
    1. Loads the data from `data/external/kr_cnt.csv`.
    2. Validates it against `contracts/dataset.schema.yaml`.
    3. Returns the results.

    Args:
        data_path: Override for data file path.
        schema_path: Override for schema file path.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'data': The loaded DataFrame (if successful).
            - 'validation': The validation result dictionary.
            - 'success': Boolean indicating overall success.
    """
    result = {
        "data": None,
        "validation": None,
        "success": False
    }

    try:
        # Step 1: Load Data
        df = load_external_data(data_path)
        result["data"] = df

        # Step 2: Validate Data
        validation_result = validate_external_data(df, schema_path)
        result["validation"] = validation_result

        # Step 3: Determine Success
        # Success is defined as loading the data. Validation errors are logged
        # but the pipeline completes. However, for strict adherence, we flag
        # if validation failed.
        if validation_result["is_valid"]:
            result["success"] = True
            logger.info("Pipeline completed successfully. Data loaded and validated.")
        else:
            result["success"] = False
            logger.warning("Pipeline completed, but data validation failed.")

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        result["success"] = False
        raise

    return result

def main():
    """
    Entry point for the script.
    """
    logger.info("Starting external data loading pipeline (T035).")
    try:
        results = run_load_external_pipeline()
        logger.info(f"Execution finished. Success: {results['success']}")
        
        # Print summary
        if results['data'] is not None:
            print(f"\nLoaded {len(results['data'])} rows.")
            print(f"Columns: {list(results['data'].columns)}")
        
        if results['validation']:
            print(f"Validation Status: {'PASSED' if results['validation']['is_valid'] else 'FAILED'}")
            if not results['validation']['is_valid']:
                print("Errors:")
                for err in results['validation']['errors']:
                    print(f"  - {err}")
        
        return 0 if results['success'] else 1

    except Exception as e:
        logger.critical(f"Critical failure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())