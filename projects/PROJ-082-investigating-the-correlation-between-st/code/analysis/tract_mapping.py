import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def normalize_string(s: str) -> str:
    """Normalize a string for comparison."""
    if not s:
        return ""
    return re.sub(r'\s+', ' ', s.lower().strip())

def map_to_jhu(tract_name: str) -> str:
    """
    Map a tract name to a standard JHU Atlas name.
    This is a simplified mapping for demonstration.
    """
    normalized = normalize_string(tract_name)
    
    # Define common variations and their standard names
    mappings = {
        "arcuate fasciculus": "Arcuate Fasciculus",
        "cingulum bundle": "Cingulum Bundle",
        "cingulum": "Cingulum Bundle",
        "uncinate fasciculus": "Uncinate Fasciculus",
        "inferior longitudinal fasciculus": "Inferior Longitudinal Fasciculus",
        "ilf": "Inferior Longitudinal Fasciculus",
        "auditory cortex": "Auditory Cortex",
        "ventral striatum": "Ventral Striatum",
        "corpus callosum": "Corpus Callosum",
        "genu of corpus callosum": "Corpus Callosum (Genu)",
        "splenium of corpus callosum": "Corpus Callosum (Splenium)",
        "superior longitudinal fasciculus": "Superior Longitudinal Fasciculus",
        "slf": "Superior Longitudinal Fasciculus",
        "inferior fronto-occipital fasciculus": "Inferior Fronto-Occipital Fasciculus",
        "ifof": "Inferior Fronto-Occipital Fasciculus",
        "fronto-occipital fasciculus": "Inferior Fronto-Occipital Fasciculus",
    }
    
    # Check for exact match first
    if normalized in mappings:
        return mappings[normalized]
    
    # Check for substring match
    for key, value in mappings.items():
        if key in normalized:
            return value
    
    # If no match found, return the normalized name as is
    # This ensures we don't lose data, even if it's not in our standard list
    return tract_name

def harmonize_tract_list(tract_names: List[str]) -> List[str]:
    """
    Harmonize a list of tract names using the JHU Atlas mapping.
    """
    harmonized = []
    for name in tract_names:
        if name:
            harmonized_name = map_to_jhu(name)
            harmonized.append(harmonized_name)
        else:
            logger.warning(f"Empty tract name encountered in list: {tract_names}")
    return harmonized

def load_tract_mapping_config() -> Dict[str, Any]:
    """
    Load the tract mapping configuration.
    Currently, this returns an empty dict as the logic is hardcoded.
    """
    return {}

def get_standard_tract_names() -> List[str]:
    """
    Return a list of standard tract names based on the JHU Atlas.
    """
    return [
        "Arcuate Fasciculus",
        "Cingulum Bundle",
        "Uncinate Fasciculus",
        "Inferior Longitudinal Fasciculus",
        "Auditory Cortex",
        "Ventral Striatum",
        "Corpus Callosum",
        "Superior Longitudinal Fasciculus",
        "Inferior Fronto-Occipital Fasciculus"
    ]

def main():
    """
    Entry point for script execution.
    """
    test_names = [
        "arcuate fasciculus",
        "cingulum",
        "ILF",
        "uncinate fasciculus",
        "unknown tract"
    ]
    
    print("Testing tract harmonization:")
    for name in test_names:
        print(f"  {name} -> {map_to_jhu(name)}")

if __name__ == "__main__":
    main()
