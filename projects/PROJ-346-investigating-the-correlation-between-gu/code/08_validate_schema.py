import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils import get_contracts_path, get_data_raw_path, get_data_processed_path, setup_logger
from code.schemas import MicrobialTaxa, CognitiveScore

logger = setup_logger("validate_schema")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the dataset schema definition from a YAML file.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_microbiome_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a microbiome dataframe against the schema.
    Returns a list of validation error messages.
    """
    errors = []
    schema_props = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")

    # Check column types and constraints based on schema
    for col in df.columns:
        if col in schema_props:
            col_schema = schema_props[col]
            dtype = col_schema.get("type")
            
            # Basic type checking
            if dtype == "number" and not pd.api.types.is_numeric_dtype(df[col]):
                # Allow object columns that can be converted to numeric for taxonomic strings usually
                # But if it's supposed to be abundance/read count, it must be numeric
                if "abundance" in col.lower() or "read" in col.lower():
                    errors.append(f"Column '{col}' should be numeric but is {df[col].dtype}")
            
            # Check for nulls if not allowed
            if not col_schema.get("nullable", True) and df[col].isnull().any():
                errors.append(f"Column '{col}' contains null values but schema does not allow it")

    # Specific microbiome checks
    if "sample_id" in df.columns:
        if df["sample_id"].duplicated().any():
            errors.append("Duplicate sample_ids found in microbiome data")

    return errors

def validate_cognitive_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a cognitive dataframe against the schema.
    Returns a list of validation error messages.
    """
    errors = []
    schema_props = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")

    # Check column types
    for col in df.columns:
        if col in schema_props:
            col_schema = schema_props[col]
            dtype = col_schema.get("type")
            
            if dtype == "number" and not pd.api.types.is_numeric_dtype(df[col]):
                if "score" in col.lower() or "time" in col.lower():
                    errors.append(f"Column '{col}' should be numeric but is {df[col].dtype}")

    return errors

def validate_file_against_schema(file_path: Path, schema_name: str) -> bool:
    """
    Load a parquet file and validate it against the corresponding schema definition.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        logger.error(f"Failed to read parquet file {file_path}: {e}")
        return False

    schema_path = get_contracts_path() / "dataset.schema.yaml"
    if not schema_path.exists():
        logger.error(f"Schema definition file not found at {schema_path}")
        return False

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # Select the specific schema from the combined file
    if schema_name not in schema:
        logger.error(f"Schema definition for '{schema_name}' not found in {schema_path}")
        return False

    target_schema = schema[schema_name]
    
    logger.info(f"Validating {file_path.name} against {schema_name} schema...")

    if "microbiome" in schema_name.lower():
        errors = validate_microbiome_schema(df, target_schema)
    elif "cognitive" in schema_name.lower():
        errors = validate_cognitive_schema(df, target_schema)
    else:
        # Generic fallback: just check required fields if defined
        errors = []
        for field in target_schema.get("required", []):
            if field not in df.columns:
                errors.append(f"Missing required column: {field}")

    if errors:
        logger.error(f"Validation FAILED for {file_path.name}:")
        for err in errors:
            logger.error(f"  - {err}")
        return False
    else:
        logger.info(f"Validation PASSED for {file_path.name}")
        return True

def main():
    """
    Main entry point to validate output parquet files against the schema.
    """
    contracts_path = get_contracts_path()
    raw_path = get_data_raw_path()
    processed_path = get_data_processed_path()

    all_valid = True

    # Define files to validate based on T011, T012, T013 outputs
    files_to_check = [
        (raw_path / "microbiome_raw.parquet", "microbiome_raw"),
        (raw_path / "cognitive_raw.parquet", "cognitive_raw"),
        (processed_path / "cognitive_processed.parquet", "cognitive_processed"),
    ]

    # Check for merged file if it exists
    merged_path = processed_path / "merged_dataset.parquet"
    if merged_path.exists():
        files_to_check.append((merged_path, "merged_dataset"))

    for file_path, schema_name in files_to_check:
        if file_path.exists():
            if not validate_file_against_schema(file_path, schema_name):
                all_valid = False
        else:
            logger.warning(f"File not found, skipping validation: {file_path}")

    if not all_valid:
        logger.error("Schema validation failed for one or more files.")
        sys.exit(1)
    else:
        logger.info("All existing output files passed schema validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()
