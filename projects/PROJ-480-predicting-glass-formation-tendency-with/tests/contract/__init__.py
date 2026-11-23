"""
Contract test utilities for schema validation.
"""
import yaml
from pathlib import Path
import sys

# Ensure parent directory is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))


def load_schema(schema_name: str) -> dict:
    """
    Load a JSON schema from the tests/contract directory.
    
    Args:
        schema_name: Name of the schema file (without .yaml extension)
    
    Returns:
        Dictionary containing the loaded schema
    
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        yaml.YAMLError: If the schema file is invalid YAML
    """
    schema_path = Path(__file__).parent / f"{schema_name}.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema
