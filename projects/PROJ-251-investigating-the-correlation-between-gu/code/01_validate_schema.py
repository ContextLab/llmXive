import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

import yaml
import pandas as pd
import jsonschema
from jsonschema import validate, ValidationError

from utils.logging_config import get_logger, log_error_context
from utils.config import get_processed_path, get_specs_path

logger = get_logger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file and return it as a dictionary.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema


def validate_csv_against_schema(
    csv_path: Path, 
    schema: Dict[str, Any],
    expected_min_rows: int = 0
) -> bool:
    """
    Validate a CSV file against a JSON Schema (derived from YAML).
    
    The CSV is expected to be in 'long' format where each row is a subject.
    The schema defines the structure of a single row (object).
    
    Returns True if valid, False otherwise.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded data from {csv_path} with {len(df)} rows.")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False

    if len(df) < expected_min_rows:
        logger.warning(f"Data has {len(df)} rows, expected at least {expected_min_rows}")
        # We might still validate schema, but log the warning
    
    # Check required columns from schema
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in df.columns:
            logger.error(f"Missing required column: {field}")
            return False

    # Validate each row against the schema properties
    # We construct a minimal schema for a single row based on the provided schema
    # The provided schema is for an object. We apply it to each row (dict).
    
    row_schema = {
        "type": "object",
        "properties": schema.get('properties', {}),
        "required": required_fields,
        "additionalProperties": schema.get('additionalProperties', True)
    }

    errors = []
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        try:
            validate(instance=row_dict, schema=row_schema)
        except ValidationError as e:
            errors.append(f"Row {idx}: {e.message} (instance: {e.instance}, path: {list(e.path)})")
            if len(errors) >= 5: # Limit log spam
                errors.append("... (truncated)")
                break

    if errors:
        logger.error(f"Validation failed for {csv_path}:")
        for err in errors:
            logger.error(f"  - {err}")
        return False

    logger.info(f"Validation successful for {csv_path}")
    return True


def run_validation():
    """
    Main entry point for schema validation.
    Validates the processed dataset against the dataset.schema.yaml.
    """
    try:
        # Paths
        schema_path = get_specs_path() / "contracts" / "dataset.schema.yaml"
        data_path = get_processed_path() / "cleared_with_diversity.csv"

        logger.info(f"Starting schema validation for {data_path}")
        
        # Load Schema
        schema = load_schema(schema_path)
        
        # Validate
        is_valid = validate_csv_against_schema(
            csv_path=data_path,
            schema=schema,
            expected_min_rows=50
        )

        if is_valid:
            logger.info("Schema validation PASSED.")
            return 0
        else:
            logger.error("Schema validation FAILED.")
            return 1

    except FileNotFoundError as e:
        log_error_context(e)
        return 1
    except Exception as e:
        log_error_context(e)
        return 1


def main():
    """
    CLI entry point.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(run_validation())


if __name__ == "__main__":
    main()
