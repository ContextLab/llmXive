import json
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_schema_map() -> Dict[str, List[str]]:
    """Load the schema map from config."""
    config_path = Path("code/config/schema_map.json")
    if not config_path.exists():
        raise FileNotFoundError(f"schema_map.json not found at {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)

def get_target_columns() -> List[str]:
    """Get list of target column names."""
    schema = load_schema_map()
    return list(schema.keys())

def get_source_columns_for_target(target: str) -> List[str]:
    """Get list of source column names for a target."""
    schema = load_schema_map()
    return schema.get(target, [])

def get_mapping_for_source(source: str) -> Optional[str]:
    """Get target column for a source column."""
    schema = load_schema_map()
    for target, sources in schema.items():
        if source in sources:
            return target
    return None