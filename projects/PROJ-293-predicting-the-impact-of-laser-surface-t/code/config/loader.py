"""Loader for schema mapping configuration."""
import json
from pathlib import Path
from typing import Dict, List, Any

# Define the path relative to the project root
# Assuming this file is at code/config/loader.py
_SCHEMA_MAP_PATH = Path(__file__).parent / "schema_map.json"


def load_schema_map() -> Dict[str, List[str]]:
    """
    Load the canonical column mapping from the JSON configuration file.
    
    Returns:
        Dict mapping canonical column names to lists of possible source column names.
    
    Raises:
        FileNotFoundError: If schema_map.json does not exist.
        json.JSONDecodeError: If the JSON file is malformed.
    """
    if not _SCHEMA_MAP_PATH.exists():
        raise FileNotFoundError(
            f"Schema map configuration not found at {_SCHEMA_MAP_PATH}. "
            "Ensure T006 has created the config file."
        )
    
    with open(_SCHEMA_MAP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('mappings', {})


def get_target_columns() -> List[str]:
    """
    Retrieve the list of canonical target column names.
    
    Returns:
        List of canonical column names.
    """
    if not _SCHEMA_MAP_PATH.exists():
        raise FileNotFoundError(_SCHEMA_MAP_PATH)
        
    with open(_SCHEMA_MAP_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('target_columns', [])


def get_source_columns_for_target(target: str) -> List[str]:
    """
    Get all possible source column names that map to a specific target.
    
    Args:
        target: The canonical target column name (e.g., 'power').
        
    Returns:
        List of source column names. Empty list if target not found.
    """
    mappings = load_schema_map()
    return mappings.get(target, [])
