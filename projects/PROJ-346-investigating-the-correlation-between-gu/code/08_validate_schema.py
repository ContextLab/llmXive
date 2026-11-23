"""
Schema validation module for the microbiome-cognition correlation project.

Validates output parquet files against the dataset schema defined in 
contracts/dataset.schema.yaml using pandera.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd
import pandera as pa
from pandera.typing import Series
from typing import Dict, Any, Optional
import argparse

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.name != 'llmXive' and current != current.parent:
        current = current.parent
    return current / 'projects' / 'PROJ-346-investigating-the-correlation-between-gu'

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the YAML schema definition from file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema_def = yaml.safe_load(f)
    
    if not schema_def:
        raise ValueError("Schema file is empty or invalid YAML")
    
    return schema_def

def create_pandera_schema(schema_def: Dict[str, Any]) -> pa.DataFrameSchema:
    """
    Convert YAML schema definition to a pandera DataFrameSchema.
    
    Args:
        schema_def: Dictionary containing schema definition from YAML
        
    Returns:
        pandera DataFrameSchema object
    """
    columns = {}
    
    # Handle MicrobialTaxa schema
    if 'MicrobialTaxa' in schema_def:
        taxa_fields = schema_def['MicrobialTaxa']
        for field_name, field_props in taxa_fields.items():
            dtype = field_props.get('type', 'str')
            nullable = field_props.get('nullable', False)
            required = field_props.get('required', True)
            
            # Map YAML types to pandera dtypes
            if dtype == 'str':
                pandera_dtype = pa.String
            elif dtype == 'float':
                pandera_dtype = pa.Float
            elif dtype == 'int':
                pandera_dtype = pa.Int
            else:
                pandera_dtype = pa.Object  # Fallback for unknown types
            
            # Add checks if specified
            checks = []
            if 'min_value' in field_props:
                checks.append(pa.Check.gte(field_props['min_value']))
            if 'max_value' in field_props:
                checks.append(pa.Check.lte(field_props['max_value']))
            if 'str_length' in field_props:
                min_len = field_props['str_length'].get('min', 0)
                max_len = field_props['str_length'].get('max', None)
                checks.append(pa.Check.str_length(min_len, max_len))
            
            columns[field_name] = pa.Column(
                pandera_dtype,
                nullable=nullable,
                required=required,
                checks=checks if checks else None,
                name=field_name
            )
    
    # Handle CognitiveScore schema
    if 'CognitiveScore' in schema_def:
        cog_fields = schema_def['CognitiveScore']
        for field_name, field_props in cog_fields.items():
            dtype = field_props.get('type', 'str')
            nullable = field_props.get('nullable', False)
            required = field_props.get('required', True)
            
            if dtype == 'str':
                pandera_dtype = pa.String
            elif dtype == 'float':
                pandera_dtype = pa.Float
            elif dtype == 'int':
                pandera_dtype = pa.Int
            else:
                pandera_dtype = pa.Object
            
            checks = []
            if 'min_value' in field_props:
                checks.append(pa.Check.gte(field_props['min_value']))
            if 'max_value' in field_props:
                checks.append(pa.Check.lte(field_props['max_value']))
            
            columns[field_name] = pa.Column(
                pandera_dtype,
                nullable=nullable,
                required=required,
                checks=checks if checks else None,
                name=field_name
            )
    
    return pa.DataFrameSchema(columns, name="DatasetSchema")

def validate_file_against_schema(
    file_path: Path, 
    schema_path: Optional[Path] = None,
    schema_name: str = "DatasetSchema"
) -> bool:
    """
    Validate a parquet file against the dataset schema.
    
    Args:
        file_path: Path to the parquet file to validate
        schema_path: Optional path to schema YAML (defaults to contracts/dataset.schema.yaml)
        schema_name: Name of the schema to use (for future extensibility)
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        FileNotFoundError: If file or schema doesn't exist
        ValueError: If validation fails
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File to validate not found: {file_path}")
    
    if schema_path is None:
        contracts_path = get_project_root() / 'contracts'
        schema_path = contracts_path / 'dataset.schema.yaml'
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load schema
    logger.info(f"Loading schema from {schema_path}")
    schema_def = load_schema(schema_path)
    schema = create_pandera_schema(schema_def)
    
    # Load data
    logger.info(f"Loading data from {file_path}")
    df = pd.read_parquet(file_path)
    
    logger.info(f"Validating {len(df)} rows against schema")
    
    try:
        # Validate the dataframe
        validated_df = schema.validate(df)
        logger.info(f"Validation successful: {len(validated_df)} rows passed")
        return True
    except pa.errors.SchemaErrors as e:
        logger.error(f"Schema validation failed with {len(e.schema_errors)} errors:")
        for error in e.schema_errors:
            logger.error(f"  - {error}")
        raise ValueError(f"Schema validation failed: {e}")
    except pa.errors.SchemaError as e:
        logger.error(f"Schema validation failed: {e}")
        raise ValueError(f"Schema validation failed: {e}")

def main():
    """Main entry point for schema validation."""
    parser = argparse.ArgumentParser(
        description="Validate parquet files against dataset schema"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to parquet file to validate"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="Path to schema YAML file (default: contracts/dataset.schema.yaml)"
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    schema_path = Path(args.schema) if args.schema else None
    
    try:
        if validate_file_against_schema(file_path, schema_path):
            logger.info(f"SUCCESS: {file_path.name} passes schema validation")
            sys.exit(0)
    except Exception as e:
        logger.error(f"FAILED: {file_path.name} does not pass schema validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
