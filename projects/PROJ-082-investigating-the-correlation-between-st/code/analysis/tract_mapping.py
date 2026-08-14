import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# Standard tract mappings based on JHU Atlas and common nomenclature
# This dictionary maps variations to a canonical name
STANDARD_TRACHT_MAP = {
    "arcuate fasciculus": "arcuate fasciculus",
    "af": "arcuate fasciculus",
    "cingulum bundle": "cingulum bundle",
    "cingulum": "cingulum bundle",
    "uncinate fasciculus": "uncinate fasciculus",
    "uf": "uncinate fasciculus",
    "inferior longitudinal fasciculus": "inferior longitudinal fasciculus",
    "ilf": "inferior longitudinal fasciculus",
    "auditory cortex": "auditory cortex",
    "ventral striatum": "ventral striatum",
    "corpus callosum": "corpus callosum",
    "cc": "corpus callosum",
    "superior longitudinal fasciculus": "superior longitudinal fasciculus",
    "slf": "superior longitudinal fasciculus",
}

def normalize_string(s: str) -> str:
    """
    Normalize a string for comparison: lowercase, strip whitespace, remove extra spaces.
    """
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)
    return s

def map_to_jhu(tract_name: str) -> str:
    """
    Map a tract name to its canonical JHU Atlas equivalent.
    Returns the canonical name if found, otherwise returns the normalized input.
    """
    normalized = normalize_string(tract_name)
    if not normalized:
        return ""
    
    # Direct lookup
    if normalized in STANDARD_TRACHT_MAP:
        return STANDARD_TRACHT_MAP[normalized]
    
    # Partial match logic for robustness
    for key, value in STANDARD_TRACHT_MAP.items():
        if key in normalized or normalized in key:
            return value
    
    # If no match, return the normalized original name
    return normalized

def harmonize_tract_list(tract_names: List[str]) -> List[str]:
    """
    Apply JHU mapping to a list of tract names.
    """
    return [map_to_jhu(name) for name in tract_names]

def load_tract_mapping_config(config_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load custom tract mapping configuration if it exists.
    Falls back to the default STANDARD_TRACHT_MAP if not found.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "data" / "config" / "tract_mapping_config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_map = json.load(f)
                # Merge with defaults, custom overrides defaults
                return {**STANDARD_TRACHT_MAP, **custom_map}
        except Exception as e:
            logger.warning(f"Failed to load custom tract mapping config: {e}. Using defaults.")
            return STANDARD_TRACHT_MAP
    
    return STANDARD_TRACHT_MAP

def get_standard_tract_names() -> List[str]:
    """
    Return a list of all canonical tract names defined in the mapping.
    """
    return list(set(STANDARD_TRACHT_MAP.values()))

def main():
    """
    Utility entry point for testing harmonization.
    """
    test_names = ["AF", "cingulum", "Uncinate Fasciculus", "unknown_tract"]
    harmonized = harmonize_tract_list(test_names)
    for original, mapped in zip(test_names, harmonized):
        print(f"{original} -> {mapped}")

if __name__ == "__main__":
    main()