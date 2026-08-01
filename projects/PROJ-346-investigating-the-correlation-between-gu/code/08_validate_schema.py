import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd

from code.schemas import export_schema_definitions, validate_microbial_data, validate_cognitive_data
from code.utils import get_contracts_path, setup_logger

logger = setup_logger(__name__)

def load_schema(schema_path: Path):
    """Load the schema YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_file_against_schema(file_path: Path, schema_name: str):
    """
    Validate a parquet file against the specified schema.
    
    Args:
        file_path: Path to the parquet file.
        schema_name: Name of the schema to validate against ('MicrobialTaxa' or 'CognitiveScore').
    
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    logger.info(f"Validating {file_path} against {schema_name} schema...")
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file {file_path}: {e}")
    
    if schema_name == "MicrobialTaxa":
        validate_microbial_data(df)
    elif schema_name == "CognitiveScore":
        validate_cognitive_data(df)
    else:
        raise ValueError(f"Unknown schema name: {schema_name}")
    
    logger.info(f"Validation successful for {file_path}")
    return True

def main():
    """Main entry point for schema validation script."""
    # Ensure contracts directory exists and schema is generated
    contracts_dir = get_contracts_path()
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    schema_file = contracts_dir / "dataset.schema.yaml"
    
    # Generate schema if it doesn't exist
    if not schema_file.exists():
        logger.info("Generating schema file...")
        export_schema_definitions(schema_file)
    
    # Validate existing data files if they exist
    # This is a placeholder for actual validation logic that would be called by the pipeline
    logger.info(f"Schema ready at: {schema_file}")
    print(f"Schema file generated/validated at: {schema_file}")

if __name__ == "__main__":
    main()
