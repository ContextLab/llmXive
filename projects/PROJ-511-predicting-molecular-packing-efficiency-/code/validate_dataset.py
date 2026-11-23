import os
import sys
import logging
import yaml
import json
from typing import List, Dict, Any, Optional
import pandas as pd
from jsonschema import validate, ValidationError, Draft7Validator
from pathlib import Path

# Import project config for paths and URLs
try:
    from config import get_data_dir, get_cod_url, get_base_dir
except ImportError:
    # Fallback for direct execution if config is not in path yet
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_data_dir, get_cod_url, get_base_dir

# Import error handling utilities if available
try:
    from error_handling import DataValidationError
except ImportError:
    class DataValidationError(Exception):
        """Custom exception for data validation failures."""
        pass

# --- Logging Setup ---
# Must be tolerant of different call signatures as per API contract
def setup_logging(name: Optional[str] = None, level: int = logging.INFO):
    """
    Sets up logging for the module.
    Tolerant of:
      - setup_logging()
      - setup_logging(__name__)
      - setup_logging("string_name")
      - setup_logging(level=logging.INFO)
    """
    if name is None and level is not logging.INFO:
        # If only level was passed as kwarg, handle it
        # But signature is (name, level). If called as setup_logging(level=...), name is None.
        pass
    
    logger = logging.getLogger(name if name else "validate_dataset")
    
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# Ensure the logger is initialized early
logger = setup_logging()

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from a YAML file (since we use yaml for schema storage)."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        # The schema is stored as YAML in the project (per T004)
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validates the DataFrame against the JSON schema.
    Returns a list of error messages.
    """
    errors = []
    validator = Draft7Validator(schema)
    
    # Convert DataFrame to a list of records for validation
    # We validate row by row to get specific error context
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        # Ensure types match schema expectations (e.g., lists for principal_moments)
        # The schema expects lists, pandas might read them as strings if not parsed correctly
        # But usually CSV reads everything as string, so we might need to cast.
        # However, jsonschema validation on a dict of mixed types (str, float, list) is tricky if CSV didn't parse lists.
        # Let's assume the CSV has proper types or we cast them here.
        
        # Specific casting for known list fields
        if 'principal_moments' in row_dict and isinstance(row_dict['principal_moments'], str):
            try:
                import ast
                row_dict['principal_moments'] = ast.literal_eval(row_dict['principal_moments'])
            except:
                errors.append(f"Row {idx}: Invalid format for principal_moments")
                continue

        for error in validator.iter_errors(row_dict):
            errors.append(f"Row {idx}: {error.message} at {error.json_path}")
    
    return errors

def cross_reference_cif_ids(csv_path: str, cif_dir: str) -> List[str]:
    """
    Cross-references COD IDs in the CSV against the list of downloaded CIF files.
    Returns a list of missing CIF file paths.
    """
    logger.info(f"Cross-referencing CSV IDs with CIF directory: {cif_dir}")
    
    if not os.path.exists(cif_dir):
        logger.warning(f"CIF directory does not exist: {cif_dir}")
        return []

    df = pd.read_csv(csv_path)
    if 'cod_id' not in df.columns:
        raise DataValidationError("CSV must contain 'cod_id' column for cross-referencing")

    csv_ids = set(df['cod_id'].astype(str).unique())
    cif_ids = set()
    
    # Scan directory for CIF files
    for filename in os.listdir(cif_dir):
        if filename.lower().endswith('.cif'):
            # Extract COD ID from filename (assuming format COD-XXXXXXX.cif)
            # The filename might be just the ID or have a prefix.
            # We expect the cod_id in CSV to match the filename stem.
            base_name = os.path.splitext(filename)[0]
            # Normalize: ensure it matches the CSV format "COD-..."
            if base_name.startswith("COD-"):
                cif_ids.add(base_name)
            else:
                # Try to infer if the filename is the ID
                cif_ids.add(base_name)

    missing = csv_ids - cif_ids
    if missing:
        logger.warning(f"Found {len(missing)} COD IDs in CSV without corresponding CIF files.")
        # Log first 10 for brevity
        for m in list(missing)[:10]:
            logger.warning(f"  Missing: {m}")
    
    return list(missing)

def validate_dataset(csv_path: str, schema_path: str, cif_dir: str) -> bool:
    """
    Main validation logic:
    1. Check schema compliance.
    2. Cross-reference COD IDs.
    3. Verify source URL metadata (log it).
    """
    logger.info(f"Starting validation for {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    
    # 1. Schema Validation
    try:
        schema = load_schema(schema_path)
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded dataset: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        return False

    # Log Source URL as per FR-017
    cod_url = get_cod_url()
    logger.info(f"Verifying against COD Source URL: {cod_url}")

    schema_errors = validate_schema(df, schema)
    if schema_errors:
        logger.error(f"Schema validation failed with {len(schema_errors)} errors.")
        for err in schema_errors[:5]:
            logger.error(f"  {err}")
        return False

    logger.info("Schema validation passed.")

    # 2. Cross-reference CIF IDs
    missing_cifs = cross_reference_cif_ids(csv_path, cif_dir)
    if missing_cifs:
        # This is a warning, not necessarily a hard failure if the data was already processed,
        # but FR-017 implies data integrity check. We'll treat missing source files as a failure for integrity.
        logger.error(f"Data Integrity Failed: {len(missing_cifs)} records missing source CIF files.")
        return False

    logger.info("Cross-reference validation passed.")

    # 3. Log count of valid records
    logger.info(f"Validation successful. Total valid records: {len(df)}")
    return True

def main():
    """
    Entry point for the validation script.
    Reads data/dataset.csv, validates against contracts/dataset.schema.yaml,
    and cross-references with data/raw_cif/.
    """
    # Configure logging
    setup_logging()

    base_dir = get_base_dir()
    data_dir = get_data_dir()
    
    csv_path = os.path.join(data_dir, "dataset.csv")
    schema_path = os.path.join(base_dir, "contracts", "dataset.schema.yaml")
    cif_dir = os.path.join(data_dir, "raw_cif")

    logger.info(f"Base Dir: {base_dir}")
    logger.info(f"Data Dir: {data_dir}")
    logger.info(f"CSV Path: {csv_path}")
    logger.info(f"Schema Path: {schema_path}")
    logger.info(f"CIF Dir: {cif_dir}")

    success = False
    try:
        success = validate_dataset(csv_path, schema_path, cif_dir)
    except Exception as e:
        logger.critical(f"Validation process crashed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    if success:
        logger.info("T019: Dataset validation completed successfully.")
        sys.exit(0)
    else:
        logger.error("T019: Dataset validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
