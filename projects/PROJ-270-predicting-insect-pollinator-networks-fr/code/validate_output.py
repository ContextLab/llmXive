"""
Output Validation Module for Insect Pollinator Network Prediction.

This module provides functions to validate the processed dataset output
against the schema defined in code/contracts/dataset.schema.yaml.
It ensures that the preprocessing pipeline produces data that conforms
to the expected structure and metadata requirements.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import yaml
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator

from config import get_data_processed, get_project_root
from utils.logger import get_logger

logger = get_logger(__name__)


def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the JSON schema from the YAML file.

    Args:
        schema_path: Optional path to the schema file. Defaults to
                     code/contracts/dataset.schema.yaml.

    Returns:
        Dictionary representing the JSON schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        project_root = get_project_root()
        schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    logger.info(f"Successfully loaded schema from {schema_path}")
    return schema


def load_output_data(output_path: Optional[Path] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Load the processed output data (JSON) and separate metadata from data.

    Args:
        output_path: Optional path to the output file. Defaults to
                     data/processed/feature_matrix.json.

    Returns:
        Tuple of (metadata_dict, data_rows_list).

    Raises:
        FileNotFoundError: If the output file does not exist.
        json.JSONDecodeError: If the output file is not valid JSON.
    """
    if output_path is None:
        data_processed = get_data_processed()
        output_path = data_processed / "feature_matrix.json"

    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found at {output_path}")

    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'metadata' not in data or 'data' not in data:
        raise ValueError("Output JSON must contain 'metadata' and 'data' keys.")

    logger.info(f"Successfully loaded output data from {output_path}")
    return data['metadata'], data['data']


def validate_structure(metadata: Dict[str, Any], data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the output structure against the schema.

    Args:
        metadata: The metadata dictionary from the output.
        data: The list of data rows from the output.
        schema: The loaded JSON schema.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    is_valid = True

    # Reconstruct the full object for validation
    full_output = {
        'metadata': metadata,
        'data': data
    }

    try:
        # Validate against the schema
        validate(instance=full_output, schema=schema)
        logger.info("Output structure validation PASSED.")
    except ValidationError as e:
        is_valid = False
        error_msg = f"Schema validation failed: {e.message}"
        errors.append(error_msg)
        logger.error(error_msg)

    # Additional programmatic checks beyond schema

    # 1. Check metadata counts consistency
    if 'total_pairs' in metadata and 'positive_pairs' in metadata and 'negative_pairs' in metadata:
        calculated_total = metadata['positive_pairs'] + metadata['negative_pairs']
        if metadata['total_pairs'] != calculated_total:
            msg = f"Metadata inconsistency: total_pairs ({metadata['total_pairs']}) != positive ({metadata['positive_pairs']}) + negative ({metadata['negative_pairs']})."
            errors.append(msg)
            is_valid = False
            logger.error(msg)

    # 2. Check data row count matches metadata
    if 'total_pairs' in metadata and len(data) != metadata['total_pairs']:
        msg = f"Data row count ({len(data)}) does not match metadata total_pairs ({metadata['total_pairs']})."
        errors.append(msg)
        is_valid = False
        logger.error(msg)

    # 3. Verify required columns in traits for each row if schema implies specific trait columns
    # (This is a soft check; strict enforcement is in the schema 'minProperties: 1')
    if len(data) > 0:
        first_row = data[0]
        if 'traits' not in first_row or not isinstance(first_row['traits'], dict):
            msg = "First data row missing 'traits' object."
            errors.append(msg)
            is_valid = False
            logger.error(msg)

    return is_valid, errors


def main() -> int:
    """
    Main entry point for validating the preprocessing output.

    Returns:
        0 if validation passes, 1 if validation fails.
    """
    try:
        # 1. Load Schema
        schema = load_schema()

        # 2. Load Output Data
        metadata, data = load_output_data()

        # 3. Validate Structure
        is_valid, errors = validate_structure(metadata, data, schema)

        if not is_valid:
            logger.error("Validation FAILED with the following errors:")
            for err in errors:
                logger.error(f"  - {err}")
            return 1
        else:
            logger.info("Validation SUCCESSFUL. Output matches schema.")
            return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in output file: {e}")
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in schema file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
