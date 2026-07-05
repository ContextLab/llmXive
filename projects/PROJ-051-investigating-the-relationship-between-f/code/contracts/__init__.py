"""
Contracts module for validating analysis output schemas.
"""
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "analysis_output.schema.yaml"

def load_schema():
    """Load the JSON schema from the YAML file."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required to load schemas. Install via: pip install pyyaml")
    
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)