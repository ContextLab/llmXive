import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

def normalize_string(s: str) -> str:
    """Normalize a string for comparison."""
    return re.sub(r'[^a-z0-9]', '', s.lower())

def map_to_jhu(tract_name: str, mapping: Optional[Dict[str, str]] = None) -> str:
    """Map a tract name to its JHU Atlas standard name."""
    if mapping is None:
        mapping = load_tract_mapping_config()
    
    normalized = normalize_string(tract_name)
    
    for key, value in mapping.items():
        if normalize_string(key) == normalized:
            return value
    
    # Return original if no mapping found
    return tract_name

def harmonize_tract_list(tract_list: List[str], mapping: Optional[Dict[str, str]] = None) -> List[str]:
    """Harmonize a list of tract names to JHU Atlas standards."""
    return [map_to_jhu(tract, mapping) for tract in tract_list]

def load_tract_mapping_config() -> Dict[str, str]:
    """Load the tract mapping configuration."""
    config_path = Path(__file__).parent.parent.parent / "data" / "config" / "tract_mapping.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Default mapping
    return {
        "arcuate": "Arcuate Fasciculus",
        "cingulum": "Cingulum Bundle",
        "uncinate": "Uncinate Fasciculus",
        "slf": "Superior Longitudinal Fasciculus",
        "ilf": "Inferior Longitudinal Fasciculus",
        "ift": "Inferior Frontotemporal Tract",
        "cc": "Corpus Callosum",
        "cst": "Corticospinal Tract",
    }

def get_standard_tract_names() -> List[str]:
    """Get a list of standard tract names from JHU Atlas."""
    mapping = load_tract_mapping_config()
    return list(set(mapping.values()))

def main() -> None:
    """Main entry point for tract mapping."""
    import argparse
    parser = argparse.ArgumentParser(description="Tract mapping utility")
    parser.add_argument("--tract", type=str, help="Tract name to map")
    args = parser.parse_args()
    
    if args.tract:
        print(f"Mapped: {args.tract} -> {map_to_jhu(args.tract)}")
    else:
        print("Standard tract names:", get_standard_tract_names())

if __name__ == "__main__":
    main()