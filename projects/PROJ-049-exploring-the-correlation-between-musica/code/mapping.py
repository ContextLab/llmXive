"""
Genre Mapping Module (T014).

Loads a lookup table from `contracts/genre_lookup.yaml` and provides
functionality to map raw genre tags to standard categories.
Unmapped tags are categorized as 'Other'.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import logging setup from existing utils module
from utils import setup_logging

logger = setup_logging()


def load_genre_lookup(lookup_path: str = "contracts/genre_lookup.yaml") -> Dict[str, str]:
    """
    Load the genre mapping lookup table from a YAML file.

    Args:
        lookup_path: Relative path to the YAML file containing the mapping.

    Returns:
        A dictionary mapping raw genre tags (lowercase) to standard categories.

    Raises:
        FileNotFoundError: If the lookup file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    path = Path(lookup_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Genre lookup file not found at: {lookup_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected genre_lookup.yaml to contain a mapping, got {type(data)}")

    # Normalize keys to lowercase for case-insensitive matching
    normalized_map = {str(k).lower(): str(v) for k, v in data.items()}
    
    logger.info(f"Loaded {len(normalized_map)} genre mappings from {lookup_path}")
    return normalized_map


def map_genre(raw_tag: str, lookup: Dict[str, str]) -> str:
    """
    Map a single raw genre tag to a standard category.

    Args:
        raw_tag: The raw genre string from the dataset.
        lookup: The dictionary of mappings loaded via `load_genre_lookup`.

    Returns:
        The mapped standard category, or 'Other' if no match is found.
    """
    if not isinstance(raw_tag, str):
        raw_tag = str(raw_tag)
    
    key = raw_tag.strip().lower()
    
    if not key:
        return "Other"
    
    return lookup.get(key, "Other")


def map_genres_batch(raw_tags: List[str], lookup: Dict[str, str]) -> List[str]:
    """
    Map a list of raw genre tags to standard categories.

    Args:
        raw_tags: A list of raw genre strings.
        lookup: The dictionary of mappings.

    Returns:
        A list of mapped standard categories.
    """
    return [map_genre(tag, lookup) for tag in raw_tags]


def apply_genre_mapping(df: Any, raw_column: str = "raw_genre", target_column: str = "standard_genre", lookup_path: str = "contracts/genre_lookup.yaml") -> Any:
    """
    Apply genre mapping to a pandas DataFrame column.

    Args:
        df: The pandas DataFrame.
        raw_column: The name of the column containing raw genre tags.
        target_column: The name of the new column to create.
        lookup_path: Path to the genre lookup YAML file.

    Returns:
        The DataFrame with the new mapped column added.
    """
    try:
        import pandas as pd
        if not isinstance(df, pd.DataFrame):
            raise TypeError("apply_genre_mapping requires a pandas DataFrame")
    except ImportError:
        raise ImportError("pandas is required to use apply_genre_mapping")

    lookup = load_genre_lookup(lookup_path)
    
    logger.info(f"Mapping column '{raw_column}' to '{target_column}' using {len(lookup)} rules")
    
    df[target_column] = df[raw_column].apply(lambda x: map_genre(x, lookup))
    
    # Log distribution summary
    distribution = df[target_column].value_counts()
    logger.debug(f"Mapping distribution:\n{distribution}")
    
    return df