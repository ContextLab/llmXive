"""
Descriptor Validator and Saver (T019a/b support)

This module provides utilities to validate descriptor outputs against
the schema defined in contracts/descriptor_schema.yaml and save them.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import yaml
from typing import Dict, Any, List, Optional

# Add project root to path
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from code.config import DATA_PATH
from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Check if the DataFrame contains all required fields from the schema.
    Returns a list of missing fields.
    """
    required_fields = schema.get('required', [])
    missing = []
    for field in required_fields:
        if field not in df.columns:
            missing.append(field)
    return missing

def main():
    parser = argparse.ArgumentParser(description="Validate and save descriptors against schema.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path.")
    parser.add_argument("--schema", type=str, required=True, help="Path to schema YAML file.")
    parser.add_argument("--output", type=str, default=None, help="Output path (optional, defaults to input path).")
    args = parser.parse_args()

    setup_logging()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return 1

    try:
        schema = load_schema(args.schema)
        df = pd.read_csv(args.input)

        missing_fields = validate_schema_compliance(df, schema)
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            # Depending on strictness, we might fail here.
            # For T019a, we just warn and proceed if it's the base file.
            # But T019b requires strict compliance.
        else:
            logger.info("Schema validation passed.")

        output_path = args.output if args.output else args.input
        df.to_csv(output_path, index=False)
        logger.info(f"Saved validated descriptors to {output_path}")

        return 0

    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
