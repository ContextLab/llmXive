"""
Genre Mapping Module.

Loads a lookup table and maps raw genre tags to standard categories.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import setup_logging

logger = setup_logging(__name__)
CONTRACTS_DIR = Path("contracts")
LOOKUP_FILE = CONTRACTS_DIR / "genre_lookup.yaml"

def load_genre_lookup() -> Dict[str, str]:
    """
    Load genre lookup table from YAML.
    
    Returns:
        Dictionary mapping raw tags to standard genres.
    """
    if not LOOKUP_FILE.exists():
        logger.warning(f"Lookup file {LOOKUP_FILE} not found. Returning empty mapping.")
        return {}
    
    with open(LOOKUP_FILE, 'r') as f:
        data = yaml.safe_load(f)
        return data.get('mapping', {})

def map_genre(raw_tag: str, mapping: Dict[str, str]) -> str:
    """
    Map a single raw tag to a standard genre.
    
    Args:
        raw_tag: Raw genre tag.
        mapping: Lookup dictionary.
        
    Returns:
        Standard genre or 'Other'.
    """
    if not raw_tag or not isinstance(raw_tag, str):
        return "Other"
    return mapping.get(raw_tag.lower().strip(), "Other")

def map_genres_batch(tags: List[str], mapping: Dict[str, str]) -> List[str]:
    """
    Map a list of raw tags to standard genres.
    
    Args:
        tags: List of raw genre tags.
        mapping: Lookup dictionary.
        
    Returns:
        List of standard genres.
    """
    return [map_genre(tag, mapping) for tag in tags]

def apply_genre_mapping(series: Any) -> Any:
    """
    Apply genre mapping to a pandas Series or single value.
    
    Args:
        series: Input data (string, list, or Series).
        
    Returns:
        Mapped data.
    """
    mapping = load_genre_lookup()
    
    if isinstance(series, str):
        return map_genre(series, mapping)
    elif isinstance(series, list):
        return map_genres_batch(series, mapping)
    else:
        # Assume it's a pandas Series or iterable
        return [map_genre(str(x), mapping) for x in series]
