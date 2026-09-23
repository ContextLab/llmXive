"""
Configuration loader for schema standardization.
Reads the canonical column mapping from code/config/schema_map.json.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Define the path to the schema map relative to the project root
# Assuming this file is in code/config/, and schema_map.json is in the same directory
SCHEMA_MAP_PATH = Path(__file__).parent / "schema_map.json"

_schema_cache: Optional[Dict[str, Any]] = None

def load_schema_map() -> Dict[str, Any]:
    """
    Load the schema mapping configuration from the JSON file.
    Caches the result in memory to avoid repeated disk I/O.
    
    Returns:
        Dict containing 'mappings' and 'target_columns'.
    
    Raises:
        FileNotFoundError: If schema_map.json does not exist.
        json.JSONDecodeError: If the JSON file is malformed.
    """
    global _schema_cache
    if _schema_cache is not None:
        return _schema_cache
    
    if not SCHEMA_MAP_PATH.exists():
        raise FileNotFoundError(f"Schema map file not found at {SCHEMA_MAP_PATH}")
    
    with open(SCHEMA_MAP_PATH, 'r', encoding='utf-8') as f:
        _schema_cache = json.load(f)
    
    return _schema_cache

def get_target_columns() -> List[str]:
    """
    Retrieve the list of canonical target column names.
    
    Returns:
        List of target column names (e.g., ['power', 'hardness', ...]).
    """
    schema = load_schema_map()
    return schema.get("target_columns", [])

def get_source_columns_for_target(target_col: str) -> List[str]:
    """
    Retrieve the list of potential source column names for a given target column.
    
    Args:
        target_col: The canonical target column name (e.g., 'power').
    
    Returns:
        List of source column names that map to the target.
    
    Raises:
        KeyError: If the target column is not found in the mapping.
    """
    schema = load_schema_map()
    mappings = schema.get("mappings", {})
    if target_col not in mappings:
        raise KeyError(f"Target column '{target_col}' not found in schema mappings.")
    return mappings[target_col]

def get_mapping_for_source(source_col: str) -> Optional[str]:
    """
    Find the canonical target column for a given source column name.
    Iterates through the mappings to find the first match.
    
    Args:
        source_col: The source column name found in raw data.
    
    Returns:
        The canonical target column name, or None if no mapping exists.
    """
    schema = load_schema_map()
    mappings = schema.get("mappings", {})
    source_lower = source_col.lower()
    
    for target, sources in mappings.items():
        # Check if the source column matches any in the list (case-insensitive)
        if any(s.lower() == source_lower for s in sources):
            return target
    
    return None
