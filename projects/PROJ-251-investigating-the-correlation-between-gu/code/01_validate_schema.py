"""
T017: Validation Gate - Validate output against dataset schema.

This script validates the filtered dataset (data/processed/filtered_data.csv)
against the schema defined in specs/.../contracts/dataset.schema.yaml.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import yaml
import jsonschema

from utils.config import get_processed_path, get_specs_path
from utils.logging_config import get_logger, log_error_context

# Configure logger
logger = get_logger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        # The schema is stored as YAML but represents a JSON schema
        schema = yaml.safe_load(f)
    return schema


def validate_csv_against_schema(data_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate the CSV data against the loaded schema.

    The schema expects a structure like:
    {
      "metadata": {...},
      "data": [ {...}, ... ]
    }

    We need to transform the CSV into this structure for validation.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Construct the document structure expected by the schema
    # The schema expects 'data' to be a list of objects (rows)
    # and 'metadata' to contain summary info.

    rows = []
    for _, row in df.iterrows():
        # Convert row to dict
        record = row.to_dict()

        # Handle baseline_microbiome if it's a string representation of JSON
        # The schema expects 'baseline_microbiome' to be an object (dict)
        # If the CSV stores it as a string, we need to parse it or handle it.
        # Assuming the CSV has separate columns for taxa or a JSON string.
        # Based on the schema, 'baseline_microbiome' is an object.
        # If the CSV has flattened columns (e.g., taxon_A, taxon_B),
        # we might need to reconstruct it.
        # However, standard CSVs don't nest objects well.
        # Let's assume the CSV has a column 'baseline_microbiome' containing a JSON string
        # or the schema validation is meant for a JSON output.
        #
        # Given the schema requires 'baseline_microbiome' as an object:
        # If the CSV column exists as a stringified JSON, parse it.
        if 'baseline_microbiome' in record:
            val = record['baseline_microbiome']
            if isinstance(val, str):
                try:
                    record['baseline_microbiome'] = json.loads(val)
                except json.JSONDecodeError:
                    # If it's not valid JSON, it might be a representation error
                    # or the data structure is different.
                    # For strict schema validation, we must ensure it's an object.
                    # If it's just a string of taxa names, this might fail schema.
                    # We'll let jsonschema raise the error if it's not a dict.
                    pass

        rows.append(record)

    # Construct metadata from the file path or existing data if present
    # If the CSV doesn't have metadata, we construct a minimal one.
    document = {
        "metadata": {
            "source": "SRP053178", # Default source based on project context
            "subjects_total": len(rows),
            "timestamp": pd.Timestamp.now().isoformat()
        },
        "data": rows
    }

    # Validate
    try:
        jsonschema.validate(instance=document, schema=schema)
        logger.info("Schema validation PASSED.")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Schema validation FAILED: {e.message}")
        logger.error(f"Path: {e.absolute_path}")
        return False


def run_validation() -> bool:
    """Main execution function for T017."""
    schema_path = get_specs_path() / "contracts" / "dataset.schema.yaml"
    data_path = get_processed_path() / "filtered_data.csv"

    logger.info(f"Validating data at: {data_path}")
    logger.info(f"Using schema at: {schema_path}")

    try:
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file missing: {schema_path}")

        schema = load_schema(schema_path)
        is_valid = validate_csv_against_schema(data_path, schema)

        # Log result
        result_file = get_processed_path() / "schema_validation_result.json"
        result_data = {
            "status": "PASS" if is_valid else "FAIL",
            "data_file": str(data_path),
            "schema_file": str(schema_path),
            "timestamp": pd.Timestamp.now().isoformat()
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2)

        logger.info(f"Validation result written to: {result_file}")

        return is_valid

    except Exception as e:
        log_error_context(logger, "Validation failed", exception=e)
        return False


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
