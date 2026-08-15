import os
import sys
import csv
import yaml
import logging
import pandas as pd
from pathlib import Path

from config import get_project_root, get_logs_dir

logger = logging.getLogger(__name__)

def setup_logger():
    """Configure logging for the schema validator module."""
    log_dir = get_logs_dir()
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        log_file = os.path.join(log_dir, 'schema_validator.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    else:
        logging.basicConfig(level=logging.INFO)

def load_schema(schema_path: str) -> dict:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate that the dataframe matches the schema defined in the YAML file.
    
    This function checks:
    1. All required columns are present.
    2. Optional columns are recognized (warnings for unexpected columns).
    3. Column data types are compatible with expected types (basic check).
    
    Args:
        df: Pandas DataFrame to validate.
        schema_path: Path to the schema YAML file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    required_cols = schema.get('required_columns', [])
    optional_cols = schema.get('optional_columns', [])
    
    all_allowed = set(required_cols + optional_cols)
    actual_cols = set(df.columns)
    
    missing_required = set(required_cols) - actual_cols
    if missing_required:
        logger.error(f"Missing required columns: {missing_required}")
        return False
    
    # Check for unexpected columns
    extra_cols = actual_cols - all_allowed
    if extra_cols:
        logger.warning(f"Found extra columns not in schema: {extra_cols}")
    
    # Basic type checking for numeric columns
    numeric_cols = required_cols + optional_cols
    for col in numeric_cols:
        if col in actual_cols:
            if not pd.api.types.is_numeric_dtype(df[col]):
                logger.warning(f"Column '{col}' is not numeric (dtype: {df[col].dtype})")
    
    logger.info("Schema validation passed.")
    return True

def validate_and_report(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate CSV schema and report results to the logger.
    
    Args:
        df: Pandas DataFrame to validate.
        schema_path: Path to the schema YAML file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    return validate_csv_schema(df, schema_path)

def main():
    """Main entry point for schema validation."""
    setup_logger()
    logger.info("Schema validator module loaded.")
    
    # Example usage for testing
    try:
        # Get the schema path relative to project root
        project_root = get_project_root()
        schema_path = os.path.join(project_root, 'contracts', 'dataset.schema.yaml')
        
        if os.path.exists(schema_path):
            logger.info(f"Schema loaded from: {schema_path}")
            # Create a dummy dataframe for demonstration
            dummy_df = pd.DataFrame({
                'laser_power': [100, 200],
                'scan_speed': [500, 600],
                'layer_thickness': [0.03, 0.04],
                'yield_strength': [300, 400],
                'ductility': [10, 15]
            })
            
            result = validate_csv_schema(dummy_df, schema_path)
            logger.info(f"Validation result: {result}")
        else:
            logger.warning(f"Schema file not found at: {schema_path}")
            
    except Exception as e:
        logger.error(f"Error during validation: {e}")

if __name__ == "__main__":
    main()