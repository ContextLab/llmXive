import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

def normalize_string(s: str) -> str:
    """Normalize a string for comparison."""
    if not s:
        return ""
    return re.sub(r'[^a-z0-9]', '', s.lower()).strip()

def map_to_jhu(tract_name: str) -> Optional[str]:
    """Map a tract name to JHU atlas standard name."""
    # Simple mapping based on common variants
    mapping = {
        "arcuate": "Arcuate Fasciculus",
        "arcuate fasciculus": "Arcuate Fasciculus",
        "af": "Arcuate Fasciculus",
        "cingulum": "Cingulum Bundle",
        "cingulum bundle": "Cingulum Bundle",
        "cg": "Cingulum Bundle",
        "uncinate": "Uncinate Fasciculus",
        "uncinate fasciculus": "Uncinate Fasciculus",
        "uf": "Uncinate Fasciculus",
        "corpus callosum": "Corpus Callosum",
        "cc": "Corpus Callosum",
        "slf": "Superior Longitudinal Fasciculus",
        "superior longitudinal fasciculus": "Superior Longitudinal Fasciculus",
        "ilf": "Inferior Longitudinal Fasciculus",
        "inferior longitudinal fasciculus": "Inferior Longitudinal Fasciculus",
        "ift": "Inferior Fronto-Occipital Fasciculus",
        "inferior fronto-occipital fasciculus": "Inferior Fronto-Occipital Fasciculus",
    }

    normalized = normalize_string(tract_name)
    return mapping.get(normalized, None)

def harmonize_tract_list(tract_list: List[str]) -> List[str]:
    """Harmonize a list of tract names to JHU standard names."""
    harmonized = []
    for tract in tract_list:
        mapped = map_to_jhu(tract)
        if mapped:
            harmonized.append(mapped)
        else:
            # Keep original if no mapping found
            harmonized.append(tract)
    return harmonized

def load_tract_mapping_config() -> Dict:
    """Load tract mapping configuration from file."""
    config_path = Path(__file__).parent.parent.parent / "data" / "tract_mapping_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def get_standard_tract_names() -> List[str]:
    """Get list of standard JHU tract names."""
    return [
        "Arcuate Fasciculus",
        "Cingulum Bundle",
        "Uncinate Fasciculus",
        "Corpus Callosum",
        "Superior Longitudinal Fasciculus",
        "Inferior Longitudinal Fasciculus",
        "Inferior Fronto-Occipital Fasciculus"
    ]

def main():
    """Main entry point for tract mapping tests."""
    test_tracts = ["arcuate", "AF", "cingulum bundle", "unc", "corpus callosum"]
    print("Testing tract mapping:")
    for t in test_tracts:
        mapped = map_to_jhu(t)
        print(f"  {t} -> {mapped}")

    harmonized = harmonize_tract_list(test_tracts)
    print(f"Harmonized list: {harmonized}")

if __name__ == "__main__":
    main()