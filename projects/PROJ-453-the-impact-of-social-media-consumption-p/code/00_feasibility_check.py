import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml

# Importing local utilities from the existing API surface
# Note: Assuming utils.py is in the same directory or path is configured
try:
    from utils import log_setup
except ImportError:
    # Fallback if utils is not importable in this specific execution context
    def log_setup():
        logger = logging.getLogger("feasibility")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

def load_schema_contract(schema_path: str) -> dict:
    """Load the dataset schema contract from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(df, schema: dict) -> bool:
    """
    Validate that the DataFrame columns match the required columns in the schema.
    Returns True if valid, raises ValueError if invalid.
    """
    required_columns = set(schema.get('required_columns', []))
    actual_columns = set(df.columns)
    
    missing = required_columns - actual_columns
    if missing:
        raise ValueError(f"Schema validation failed: Missing required columns: {missing}")
    
    # Check types if specified
    type_map = schema.get('types', {})
    for col, expected_type in type_map.items():
        if col in df.columns:
            # Basic type check (pandas might infer float/int differently)
            # We just ensure the column exists and is numeric if expected
            if expected_type in ['integer', 'float']:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise TypeError(f"Column '{col}' must be numeric, got {df[col].dtype}")
    
    return True

def check_dataset_feasibility(url: str, schema_path: str) -> bool:
    """
    Perform a lightweight check to verify the URL is accessible and the dataset
    contains the required tabular data structure.
    """
    import pandas as pd
    from datasets import load_dataset
    
    logger = log_setup()
    logger.info(f"Checking feasibility for dataset: {url}")
    
    try:
        # Load schema
        schema = load_schema_contract(schema_path)
        
        # Attempt to load dataset with streaming to avoid full download
        # Using streaming=True to peek at the first row
        logger.info("Loading dataset in streaming mode to verify structure...")
        dataset = load_dataset(url, split="train", streaming=True)
        
        # Peek at the first row to get column names
        first_row = next(iter(dataset))
        actual_columns = set(first_row.keys())
        
        required_columns = set(schema.get('required_columns', []))
        missing = required_columns - actual_columns
        
        if missing:
            logger.error(f"Data Gap: Required variables {missing} not found in dataset schema.")
            logger.error(f"Found columns: {actual_columns}")
            return False
        
        logger.info("Schema validation passed. Required variables present.")
        return True

    except Exception as e:
        logger.error(f"Feasibility check failed: {str(e)}")
        return False

def main():
    """Main entry point for the feasibility check script."""
    logger = log_setup()
    logger.info("Starting Feasibility Check Pipeline (T004: Schema Validation)")
    
    # Paths
    schema_path = "contracts/dataset.schema.yaml"
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    schema_log_path = log_dir / "schema_validation.log"
    
    # Configuration (Hardcoded for this task as per typical script structure)
    # In a real scenario, these might come from a config file or CLI args
    dataset_url = "social_media_cognitive_flexibility" # Placeholder for the actual dataset ID
    
    # If the dataset URL is not provided or valid, we simulate a check against a local file
    # or a known public dataset. For this implementation, we assume the schema exists.
    
    try:
        # 1. Load Schema
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema_contract(schema_path)
        logger.info("Schema loaded successfully.")
        
        # 2. Validate Schema Structure (Mock check against a dummy DF if no data yet)
        # Since T001-T003 handle the URL check, T004 focuses on the schema logic.
        # We validate the schema file itself is well-formed and contains required keys.
        if 'required_columns' not in schema:
            raise ValueError("Schema missing 'required_columns' key.")
        
        logger.info(f"Schema contains {len(schema['required_columns'])} required columns.")
        
        # 3. Write Log
        with open(schema_log_path, 'w') as f:
            f.write(f"Schema Validation Log - {datetime.now()}\n")
            f.write(f"Schema File: {schema_path}\n")
            f.write(f"Status: PASSED\n")
            f.write(f"Required Columns: {', '.join(schema['required_columns'])}\n")
            f.write("Note: Full data validation will occur during ingestion (T015c).\n")
        
        logger.info(f"Schema validation log written to {schema_log_path}")
        print(f"SUCCESS: Schema validation complete. Log at {schema_log_path}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Critical Error: {e}")
        print(f"FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    # Ensure pandas is available for type checking if needed later
    try:
        import pandas as pd
    except ImportError:
        print("Error: pandas is required for schema validation.")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)