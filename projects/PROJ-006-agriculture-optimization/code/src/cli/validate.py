"""
CLI tool to validate data artifacts against schema contracts.
Supports dataset, regression, and sensitivity schemas.
"""
import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml

# Import local utilities
from src.utils.io_helpers import setup_logging, load_yaml, read_csv_strict
from src.config.schemas import (
    validate_dataset_schema,
    validate_regression_output,
    AnalysisDatasetRecord,
    RegressionOutput
)

logger = setup_logging("validate")

def validate_csv_artifact(
    file_path: Path,
    schema_type: str,
    schema_path: Optional[Path] = None,
    no_strict: bool = False
) -> bool:
    """
    Validate a CSV artifact against the specified schema.

    Args:
        file_path: Path to the CSV file.
        schema_type: One of 'dataset', 'regression', 'sensitivity'.
        schema_path: Optional explicit path to a YAML schema file.
        no_strict: If True, allow missing optional columns (not implemented for core types).

    Returns:
        True if validation passes, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        if schema_type == "dataset":
            # Load CSV and validate against Pydantic model
            df = pd.read_csv(file_path)
            
            # Validate row by row or bulk if possible
            # For large files, we might sample, but for validation we check all if feasible
            # Using Pydantic's model_validate on dict records
            errors = []
            for idx, row in df.iterrows():
                try:
                    record = AnalysisDatasetRecord(**row.to_dict())
                except Exception as e:
                    errors.append(f"Row {idx}: {str(e)}")
                    if len(errors) > 5:
                        break
            
            if errors:
                logger.error(f"Validation failed for {file_path} ({len(errors)} errors):")
                for err in errors[:5]:
                    logger.error(f"  - {err}")
                return False
            
            logger.info(f"Dataset validation passed for {file_path} ({len(df)} rows)")
            return True

        elif schema_type == "regression":
            # Regression output is JSON, but if CSV is passed, treat as error or specific format
            # The task description implies validating the CSV dataset, but schema_type allows regression.
            # If a CSV is passed for regression, it's likely a mismatch unless a specific CSV schema exists.
            # Assuming JSON for regression based on T025 output.
            logger.error(f"Regression validation expects JSON, received CSV: {file_path}")
            return False

        elif schema_type == "sensitivity":
            # Sensitivity results are CSV with specific columns
            df = pd.read_csv(file_path)
            required_cols = ["threshold", "model", "coefficient", "p_value", "std_err"]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                logger.error(f"Sensitivity CSV missing columns: {missing}")
                return False
            logger.info(f"Sensitivity validation passed for {file_path}")
            return True

        else:
            logger.error(f"Unknown schema type: {schema_type}")
            return False

    except Exception as e:
        logger.error(f"Error validating {file_path}: {str(e)}")
        return False

def validate_json_artifact(
    file_path: Path,
    schema_type: str,
    schema_path: Optional[Path] = None
) -> bool:
    """
    Validate a JSON artifact against the specified schema.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if schema_type == "regression":
            try:
                # Validate against Pydantic model
                output = RegressionOutput(**data)
                logger.info(f"Regression validation passed for {file_path}")
                return True
            except Exception as e:
                logger.error(f"Regression validation failed: {str(e)}")
                return False
        
        elif schema_type == "dataset":
            # JSON dataset validation (if applicable)
            logger.error("Dataset validation is primarily for CSV. Use CSV validation.")
            return False

        else:
            logger.error(f"Unknown schema type for JSON: {schema_type}")
            return False

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error validating {file_path}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate data artifacts against schema contracts.")
    parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the file to validate (CSV or JSON)."
    )
    parser.add_argument(
        "--schema-type",
        type=str,
        required=True,
        choices=["dataset", "regression", "sensitivity"],
        help="Type of schema to validate against."
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=None,
        help="Optional path to a specific YAML contract file (if not using built-in)."
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Allow missing optional columns (future implementation)."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level."
    )

    args = parser.parse_args()

    # Re-initialize logger with correct level
    global logger
    logger = setup_logging("validate", level=args.log_level)

    if args.file_path.suffix.lower() == '.csv':
        success = validate_csv_artifact(
            args.file_path,
            args.schema_type,
            args.contract,
            args.no_strict
        )
    elif args.file_path.suffix.lower() == '.json':
        success = validate_json_artifact(
            args.file_path,
            args.schema_type,
            args.contract
        )
    else:
        logger.error(f"Unsupported file extension: {args.file_path.suffix}")
        sys.exit(1)

    if success:
        logger.info("Validation successful.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
