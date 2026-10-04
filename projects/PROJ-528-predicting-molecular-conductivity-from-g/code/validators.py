"""
Data Validation Utilities (T005)

Functions:
- validate_smiles: Validate a single SMILES string.
- check_target_range: Check if target values are within a valid range.
- validate_file: CLI interface for validating files against schemas.
"""

import logging
import sys
import os
import json
import argparse
import re
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

def validate_smiles(smiles_str: str) -> bool:
    """
    Validate a single SMILES string.
    Returns True if valid, False otherwise.
    """
    if not isinstance(smiles_str, str) or not smiles_str.strip():
        return False
    try:
        mol = Chem.MolFromSmiles(smiles_str)
        return mol is not None
    except Exception:
        return False

def check_target_range(values, min_log_range: float = 3.0) -> bool:
    """
    Check if the target values have a dynamic range of at least min_log_range orders of magnitude.
    """
    import numpy as np
    values = np.array(values)
    valid_values = values[(~np.isnan(values)) & (values > 0)]
    if len(valid_values) < 2:
        return False
    log_range = np.log10(np.max(valid_values)) - np.log10(np.min(valid_values))
    return log_range >= min_log_range

def load_schema(schema_path: str) -> dict:
    """Load a JSON or YAML schema."""
    if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        with open(schema_path, 'r') as f:
            return json.load(f)

def validate_csv_against_schema(df, schema: dict) -> bool:
    """Validate a DataFrame against a schema."""
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in df.columns:
            logger.error(f"Missing required field: {field}")
            return False
    return True

def validate_json_against_schema(data, schema: dict) -> bool:
    """Validate a JSON object against a schema."""
    # Simplified validation (can be extended with jsonschema)
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False
    return True

def validate_file(file_path: str, schema_path: str) -> bool:
    """
    Validate a file (CSV or JSON) against a schema.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    if not os.path.exists(schema_path):
        logger.error(f"Schema not found: {schema_path}")
        return False

    schema = load_schema(schema_path)

    if file_path.endswith('.csv'):
        import pandas as pd
        df = pd.read_csv(file_path)
        return validate_csv_against_schema(df, schema)
    elif file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            data = json.load(f)
        return validate_json_against_schema(data, schema)
    else:
        logger.error(f"Unsupported file type: {file_path}")
        return False

def main():
    """CLI for validating files."""
    parser = argparse.ArgumentParser(description="Validate data files against schemas.")
    parser.add_argument("--validate", type=str, required=True, help="File to validate.")
    parser.add_argument("--schema", type=str, required=True, help="Schema file.")
    args = parser.parse_args()

    if validate_file(args.validate, args.schema):
        logger.info("Validation passed.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
