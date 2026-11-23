"""
Schema verification utilities.
"""
import yaml
import os
import sys
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

def check_yamllint(schema_path: str) -> bool:
    """
    Check if yamllint is installed and validate the schema file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return False
        
    try:
        result = subprocess.run(
            ["yamllint", schema_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            logger.error(f"yamllint failed: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        logger.warning("yamllint not found. Skipping lint check.")
        return True
    except subprocess.TimeoutExpired:
        logger.error("yamllint timed out.")
        return False

def load_and_validate_schema(schema_path: str) -> dict:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        The loaded schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
            return schema
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {schema_path}: {e}")
            raise

def main():
    """
    Entry point for command-line usage.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Verify schema files.")
    parser.add_argument("schema_path", help="Path to the schema file")
    args = parser.parse_args()
    
    if check_yamllint(args.schema_path):
        print(f"yamllint passed for {args.schema_path}")
    else:
        print(f"yamllint failed for {args.schema_path}")
        sys.exit(1)
        
    try:
        schema = load_and_validate_schema(args.schema_path)
        print(f"Schema loaded successfully: {schema.get('type', 'unknown')}")
    except Exception as e:
        print(f"Failed to load schema: {e}")
        sys.exit(1)

__all__ = ["check_yamllint", "load_and_validate_schema", "main"]
