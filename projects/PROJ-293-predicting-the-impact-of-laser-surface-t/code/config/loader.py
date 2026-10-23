"""
Configuration loader utilities for the LST wear resistance pipeline.

Provides functions to load the schema mapping and query it.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

from llmxive_toolkit import paths

# Path to the JSON schema map file
_SCHEMA_MAP_PATH = Path("code/config/schema_map.json")


def load_schema_map() -> Dict[str, List[str]]:
    """
    Load the schema map from ``code/config/schema_map.json``.

    Returns
    -------
    dict
        Mapping from canonical column names to a list of possible source aliases.
    """
    if not _SCHEMA_MAP_PATH.exists():
        raise FileNotFoundError(f"Schema map not found at {_SCHEMA_MAP_PATH}")
    with _SCHEMA_MAP_PATH.open("r", encoding="utf-8") as f:
        schema_map = json.load(f)
    if not isinstance(schema_map, dict):
        raise ValueError("Schema map JSON must be an object mapping strings to lists.")
    return schema_map


def get_target_columns(schema_map: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    Return the list of canonical target column names.

    Parameters
    ----------
    schema_map : dict, optional
        If provided, use this mapping; otherwise load from file.

    Returns
    -------
    list of str
    """
    if schema_map is None:
        schema_map = load_schema_map()
    return list(schema_map.keys())


def get_source_columns_for_target(target: str, schema_map: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    Given a canonical target column name, return the list of possible source column aliases.

    Parameters
    ----------
    target : str
        Canonical column name.
    schema_map : dict, optional
        Mapping to use; loaded if None.

    Returns
    -------
    list of str
    """
    if schema_map is None:
        schema_map = load_schema_map()
    return schema_map.get(target, [])


def get_mapping_for_source(source: str, schema_map: Optional[Dict[str, List[str]]] = None) -> Optional[str]:
    """
    Given a source column name, return the canonical target column it maps to,
    or ``None`` if no mapping exists.

    Parameters
    ----------
    source : str
        Column name found in a source dataset.
    schema_map : dict, optional
        Mapping to use; loaded if None.

    Returns
    -------
    str or None
    """
    if schema_map is None:
        schema_map = load_schema_map()
    for canonical, aliases in schema_map.items():
        if source in aliases:
            return canonical
    return None
