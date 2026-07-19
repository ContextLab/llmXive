import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

def normalize_string(s: str) -> str:
    """Normalize a string for comparison by removing non-alphanumeric characters and lowercasing."""
    if not isinstance(s, str):
        return str(s)
    return re.sub(r'[^a-z0-9]', '', s.lower())

def map_to_jhu(tract_name: str, mapping: Optional[Dict[str, str]] = None) -> str:
    """
    Map a tract name to its JHU Atlas standard name.
    
    This function performs case-insensitive, whitespace-insensitive matching
    against the provided mapping keys. If no match is found, returns the
    original input string.
    
    Args:
        tract_name: The tract name to map (e.g., "Arcuate Fasciculus", "arcuate", "ARC")
        mapping: Optional custom mapping dictionary. If None, loads from config.
    
    Returns:
        The standardized JHU Atlas tract name, or the original if no mapping exists.
    """
    if mapping is None:
        mapping = load_tract_mapping_config()
    
    normalized_input = normalize_string(tract_name)
    
    # Iterate through mapping keys to find a match
    for key, value in mapping.items():
        if normalize_string(key) == normalized_input:
            return value
    
    # Return original if no mapping found
    return tract_name

def harmonize_tract_list(tract_list: List[str], mapping: Optional[Dict[str, str]] = None) -> List[str]:
    """
    Harmonize a list of tract names to JHU Atlas standards.
    
    Args:
        tract_list: List of tract names to harmonize.
        mapping: Optional custom mapping dictionary.
    
    Returns:
        List of standardized tract names.
    """
    if mapping is None:
        mapping = load_tract_mapping_config()
    
    return [map_to_jhu(tract, mapping) for tract in tract_list]

def load_tract_mapping_config() -> Dict[str, str]:
    """
    Load the tract mapping configuration from disk.
    
    Attempts to load from data/config/tract_mapping.json. If not found,
    returns a default mapping covering common tracts.
    
    Returns:
        Dictionary mapping variant names to JHU Atlas standard names.
    """
    config_path = Path(__file__).parent.parent.parent / "data" / "config" / "tract_mapping.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Fall back to default if config is corrupted
            pass
    
    # Default mapping for common tracts
    return {
        "arcuate": "Arcuate Fasciculus",
        "arcuate fasciculus": "Arcuate Fasciculus",
        "cingulum": "Cingulum Bundle",
        "cingulum bundle": "Cingulum Bundle",
        "uncinate": "Uncinate Fasciculus",
        "uncinate fasciculus": "Uncinate Fasciculus",
        "slf": "Superior Longitudinal Fasciculus",
        "superior longitudinal fasciculus": "Superior Longitudinal Fasciculus",
        "ilf": "Inferior Longitudinal Fasciculus",
        "inferior longitudinal fasciculus": "Inferior Longitudinal Fasciculus",
        "ift": "Inferior Frontotemporal Tract",
        "inferior frontotemporal tract": "Inferior Frontotemporal Tract",
        "cc": "Corpus Callosum",
        "corpus callosum": "Corpus Callosum",
        "cst": "Corticospinal Tract",
        "corticospinal tract": "Corticospinal Tract",
        "forceps major": "Forceps Major",
        "forceps minor": "Forceps Minor",
        "tapetum": "Tapetum",
        "fornix": "Fornix",
    }

def get_standard_tract_names() -> List[str]:
    """
    Get a list of standard tract names from JHU Atlas based on current config.
    
    Returns:
        List of unique standard tract names (values in the mapping).
    """
    mapping = load_tract_mapping_config()
    return list(set(mapping.values()))

def main() -> None:
    """Main entry point for tract mapping utility."""
    import argparse
    parser = argparse.ArgumentParser(description="Tract mapping utility")
    parser.add_argument("--tract", type=str, help="Tract name to map")
    parser.add_argument("--list", action="store_true", help="List standard tract names")
    args = parser.parse_args()
    
    if args.list:
        print("Standard tract names:")
        for name in sorted(get_standard_tract_names()):
            print(f"  - {name}")
    elif args.tract:
        result = map_to_jhu(args.tract)
        print(f"Mapped: {args.tract} -> {result}")
    else:
        print("Usage: python -m analysis.tract_mapping --tract <name> OR --list")

if __name__ == "__main__":
    main()
