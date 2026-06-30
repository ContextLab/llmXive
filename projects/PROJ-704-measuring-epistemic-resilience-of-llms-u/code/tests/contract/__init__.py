"""
Contract tests package for llmXive project.

This package contains tests that validate data artifacts against
predefined schema definitions to ensure data integrity throughout
the research pipeline.
"""

import yaml
from pathlib import Path
from typing import Dict, Any

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema definition from disk.
    
    Args:
        schema_path: Path to the YAML schema file.
    
    Returns:
        Dictionary representing the loaded schema.
    
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} must contain a YAML dictionary")
    
    return schema