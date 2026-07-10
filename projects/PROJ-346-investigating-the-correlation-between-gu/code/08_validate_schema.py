"""
Task T016: Add validation to ensure output parquet files match contracts/dataset.schema.yaml.

This script loads processed parquet files from data/processed/, validates them against
the schema defined in contracts/dataset.schema.yaml, and reports any mismatches.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd
import json

# Add project root to path to import local modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import get_data_processed_path, get_contracts_path, setup_logger, get_logger
from schemas import MicrobialTaxa, CognitiveScore

# Setup logging
setup_logger("validation", level=logging.INFO)
logger = get_logger("validation")

SCHEMA_FILE = "dataset.schema.yaml"
MICROBIOME_OUTPUT = "microbiome_processed.parquet"
COGNITIVE_OUTPUT = "cognitive_processed.parquet"

def load_schema(schema_path: Path) -> dict:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_microbiome_schema(df: pd.DataFrame, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate microbiome dataframe against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    expected_schema = schema.get("MicrobialTaxa", {})
    
    # Check required columns
    required_columns = expected_schema.get("required_columns", [])
    actual_columns = set(df.columns)
    
    for col in required_columns:
        if col not in actual_columns:
            errors.append(f"Missing required column: {col}")
    
    # Check data types for specific columns if defined
    type_mapping = expected_schema.get("column_types", {})
    for col, expected_type in type_mapping.items():
        if col in actual_columns:
            actual_dtype = str(df[col].dtype)
            # Simple type mapping for validation
            type_map = {
                'int': ['int64', 'int32', 'Int64'],
                'float': ['float64', 'float32'],
                'str': ['object', 'string'],
                'datetime': ['datetime64[ns]']
            }
            
            is_valid_type = False
            for py_type, pandas_types in type_map.items():
                if expected_type.lower() == py_type:
                    if actual_dtype in pandas_types:
                        is_valid_type = True
                        break
            
            if not is_valid_type:
                errors.append(f"Column '{col}' has type {actual_dtype}, expected {expected_type}")

    # Validate specific constraints if defined (e.g., non-negative values for abundance)
    constraints = expected_schema.get("constraints", [])
    for constraint in constraints:
        col = constraint.get("column")
        if col in actual_columns:
            if constraint.get("type") == "non_negative":
                if (df[col] < 0).any():
                    errors.append(f"Column '{col}' contains negative values")
            elif constraint.get("type") == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                if min_val is not None and (df[col] < min_val).any():
                    errors.append(f"Column '{col}' contains values below {min_val}")
                if max_val is not None and (df[col] > max_val).any():
                    errors.append(f"Column '{col}' contains values above {max_val}")

    return len(errors) == 0, errors

def validate_cognitive_schema(df: pd.DataFrame, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate cognitive dataframe against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    expected_schema = schema.get("CognitiveScore", {})
    
    # Check required columns
    required_columns = expected_schema.get("required_columns", [])
    actual_columns = set(df.columns)
    
    for col in required_columns:
        if col not in actual_columns:
            errors.append(f"Missing required column: {col}")
    
    # Check data types
    type_mapping = expected_schema.get("column_types", {})
    for col, expected_type in type_mapping.items():
        if col in actual_columns:
            actual_dtype = str(df[col].dtype)
            type_map = {
                'int': ['int64', 'int32', 'Int64'],
                'float': ['float64', 'float32'],
                'str': ['object', 'string'],
                'datetime': ['datetime64[ns]']
            }
            
            is_valid_type = False
            for py_type, pandas_types in type_map.items():
                if expected_type.lower() == py_type:
                    if actual_dtype in pandas_types:
                        is_valid_type = True
                        break
            
            if not is_valid_type:
                errors.append(f"Column '{col}' has type {actual_dtype}, expected {expected_type}")

    # Validate constraints
    constraints = expected_schema.get("constraints", [])
    for constraint in constraints:
        col = constraint.get("column")
        if col in actual_columns:
            if constraint.get("type") == "non_null":
                if df[col].isnull().any():
                    errors.append(f"Column '{col}' contains null values")
            elif constraint.get("type") == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                if min_val is not None and (df[col] < min_val).any():
                    errors.append(f"Column '{col}' contains values below {min_val}")
                if max_val is not None and (df[col] > max_val).any():
                    errors.append(f"Column '{col}' contains values above {max_val}")

    return len(errors) == 0, errors

def main():
    """Main execution function for schema validation."""
    logger.info("Starting schema validation for processed datasets...")
    
    # Paths
    data_dir = get_data_processed_path()
    contracts_dir = get_contracts_path()
    schema_path = contracts_dir / SCHEMA_FILE
    
    # Load schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return 1
    
    # Validate Microbiome Data
    microbiome_path = data_dir / MICROBIOME_OUTPUT
    if microbiome_path.exists():
        logger.info(f"Validating microbiome data: {microbiome_path}")
        try:
            df_micro = pd.read_parquet(microbiome_path)
            is_valid, errors = validate_microbiome_schema(df_micro, schema)
            
            if is_valid:
                logger.info("Microbiome data validation PASSED")
            else:
                logger.error("Microbiome data validation FAILED:")
                for err in errors:
                    logger.error(f"  - {err}")
        except Exception as e:
            logger.error(f"Error reading or validating microbiome data: {e}")
    else:
        logger.warning(f"Microbiome data file not found: {microbiome_path}")
    
    # Validate Cognitive Data
    cognitive_path = data_dir / COGNITIVE_OUTPUT
    if cognitive_path.exists():
        logger.info(f"Validating cognitive data: {cognitive_path}")
        try:
            df_cog = pd.read_parquet(cognitive_path)
            is_valid, errors = validate_cognitive_schema(df_cog, schema)
            
            if is_valid:
                logger.info("Cognitive data validation PASSED")
            else:
                logger.error("Cognitive data validation FAILED:")
                for err in errors:
                    logger.error(f"  - {err}")
        except Exception as e:
            logger.error(f"Error reading or validating cognitive data: {e}")
    else:
        logger.warning(f"Cognitive data file not found: {cognitive_path}")
    
    logger.info("Schema validation completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
