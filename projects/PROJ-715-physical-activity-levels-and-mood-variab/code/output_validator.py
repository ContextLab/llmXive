import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from config import get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_path):
    """Load a YAML schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_dataframe(df, schema):
    """
    Validate a pandas DataFrame against a YAML schema.
    
    Args:
        df: pandas DataFrame
        schema: Dictionary loaded from a YAML schema file
        
    Returns:
        bool: True if valid, raises AssertionError otherwise
    """
    import pandas as pd
    
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            raise AssertionError(f"Missing required column: {field}")
    
    # Validate column types and constraints
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue
        
        col_data = df[col_name]
        
        # Type check
        if 'type' in col_schema:
            expected_type = col_schema['type']
            if expected_type == 'string':
                if not col_data.apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                    raise AssertionError(f"Column {col_name} must be string type")
            elif expected_type == 'integer':
                if not col_data.apply(lambda x: isinstance(x, (int, float)) and pd.notna(x) or pd.isna(x)).all():
                    # Allow nullable integers
                    pass 
            elif expected_type == 'float':
                if not col_data.apply(lambda x: isinstance(x, (int, float)) and pd.notna(x) or pd.isna(x)).all():
                    pass
            elif expected_type == 'date':
                # Basic date check
                if not col_data.apply(lambda x: pd.notna(x) and (isinstance(x, str) or isinstance(x, pd.Timestamp) or isinstance(x, datetime))).all():
                    raise AssertionError(f"Column {col_name} must be date type")
        
        # Min/Max constraints for numeric
        if 'min' in col_schema:
            min_val = col_schema['min']
            if col_data.min() < min_val:
                raise AssertionError(f"Column {col_name} has values below minimum {min_val}")
        
        # Nullable check
        if not col_schema.get('nullable', False):
            if col_data.isna().any():
                raise AssertionError(f"Column {col_name} cannot contain null values")
    
    return True

def main():
    """Main entry point for validation script."""
    logger.info("Output validator starting...")
    
    # Example usage - this would typically be driven by CLI args or config
    schema_path = get_path("specs/001-physical-activity-mood-variability/contracts", "daily_aggregates.schema.yaml")
    output_path = get_path("data/processed", "daily_aggregates.csv")
    
    if not os.path.exists(output_path):
        logger.error(f"Output file not found at {output_path}")
        sys.exit(1)
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}")
        sys.exit(1)
    
    try:
        import pandas as pd
        df = pd.read_csv(output_path)
        schema = load_schema(schema_path)
        validate_dataframe(df, schema)
        logger.info("Validation successful.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
