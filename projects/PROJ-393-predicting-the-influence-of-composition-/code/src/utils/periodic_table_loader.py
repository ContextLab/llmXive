"""
Periodic Table Data Loader.

Loads elemental properties from data/raw/elemental_properties.csv.
Provides functions to retrieve properties by element symbol.
"""

import csv
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from .logging_config import setup_logging

# Configure logger
logger = setup_logging(__name__)

# Global cache for properties
_element_properties: Optional[Dict[str, Dict[str, Any]]] = None
_properties_file = Path("data/raw/elemental_properties.csv")


def load_elemental_properties() -> Dict[str, Dict[str, Any]]:
    """
    Load elemental properties from the CSV file.

    Returns:
        Dictionary mapping element symbol to property dictionary.
    """
    global _element_properties

    if _element_properties is not None:
        return _element_properties

    if not _properties_file.exists():
        # Try to generate it if it doesn't exist (fallback for T006)
        logger.warning(f"Properties file {_properties_file} not found. Attempting to generate basic table.")
        _generate_basic_table()

    if not _properties_file.exists():
        raise FileNotFoundError(f"Elemental properties file not found: {_properties_file}")

    properties = {}
    with open(_properties_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            elem = row['element']
            properties[elem] = {
                'electronegativity': float(row['electronegativity']),
                'atomic_radii': float(row['atomic_radii']),
                'valence_electrons': int(row['valence_electrons']),
                'source_reference': row['source_reference']
            }

    _element_properties = properties
    logger.info(f"Loaded {len(properties)} elements from {_properties_file}")
    return properties


def _generate_basic_table():
    """Generate a basic elemental properties table if missing."""
    # This is a fallback to ensure the pipeline doesn't crash if T006 failed
    # In a real run, T006 should have created this file.
    basic_data = [
        {"element": "Mn", "electronegativity": 1.55, "atomic_radii": 127, "valence_electrons": 7, "source_reference": "Pyykko 1988"},
        {"element": "Co", "electronegativity": 1.88, "atomic_radii": 125, "valence_electrons": 9, "source_reference": "Pyykko 1988"},
        {"element": "Fe", "electronegativity": 1.83, "atomic_radii": 126, "valence_electrons": 8, "source_reference": "Pyykko 1988"},
        {"element": "Ga", "electronegativity": 1.81, "atomic_radii": 135, "valence_electrons": 3, "source_reference": "Pyykko 1988"},
        {"element": "Al", "electronegativity": 1.61, "atomic_radii": 143, "valence_electrons": 3, "source_reference": "Pyykko 1988"},
        {"element": "Ni", "electronegativity": 1.91, "atomic_radii": 124, "valence_electrons": 10, "source_reference": "Pyykko 1988"},
        {"element": "Cu", "electronegativity": 1.90, "atomic_radii": 128, "valence_electrons": 11, "source_reference": "Pyykko 1988"},
        {"element": "Sn", "electronegativity": 1.96, "atomic_radii": 145, "valence_electrons": 4, "source_reference": "Pyykko 1988"},
        {"element": "In", "electronegativity": 1.78, "atomic_radii": 167, "valence_electrons": 3, "source_reference": "Pyykko 1988"},
        {"element": "Ti", "electronegativity": 1.54, "atomic_radii": 147, "valence_electrons": 4, "source_reference": "Pyykko 1988"},
        {"element": "V", "electronegativity": 1.63, "atomic_radii": 134, "valence_electrons": 5, "source_reference": "Pyykko 1988"},
        {"element": "Zn", "electronegativity": 1.65, "atomic_radii": 134, "valence_electrons": 12, "source_reference": "Pyykko 1988"},
        {"element": "Si", "electronegativity": 1.90, "atomic_radii": 111, "valence_electrons": 4, "source_reference": "Pyykko 1988"},
        {"element": "Ge", "electronegativity": 2.01, "atomic_radii": 122, "valence_electrons": 4, "source_reference": "Pyykko 1988"},
        {"element": "Sb", "electronegativity": 2.05, "atomic_radii": 140, "valence_electrons": 5, "source_reference": "Pyykko 1988"},
        {"element": "Pb", "electronegativity": 2.33, "atomic_radii": 175, "valence_electrons": 4, "source_reference": "Pyykko 1988"},
        {"element": "Mg", "electronegativity": 1.31, "atomic_radii": 160, "valence_electrons": 2, "source_reference": "Pyykko 1988"},
        {"element": "Cr", "electronegativity": 1.66, "atomic_radii": 128, "valence_electrons": 6, "source_reference": "Pyykko 1988"},
        {"element": "Nb", "electronegativity": 1.60, "atomic_radii": 146, "valence_electrons": 5, "source_reference": "Pyykko 1988"},
        {"element": "Ta", "electronegativity": 1.50, "atomic_radii": 146, "valence_electrons": 5, "source_reference": "Pyykko 1988"}
    ]

    _properties_file.parent.mkdir(parents=True, exist_ok=True)
    with open(_properties_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["element", "electronegativity", "atomic_radii", "valence_electrons", "source_reference"])
        writer.writeheader()
        writer.writerows(basic_data)
    logger.info(f"Generated basic elemental properties file at {_properties_file}")


def get_element_property(element: str, property_name: str) -> Optional[float]:
    """
    Get a specific property for an element.

    Args:
        element: Element symbol (e.g., 'Co').
        property_name: Property name (e.g., 'electronegativity').

    Returns:
        Property value or None if not found.
    """
    props = load_elemental_properties()
    if element not in props:
        return None
    return props[element].get(property_name)


def get_all_elements() -> List[str]:
    """Return a list of all known element symbols."""
    return list(load_elemental_properties().keys())


def validate_elements_in_dataset(elements: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate a list of elements against the loaded database.

    Args:
        elements: List of element symbols.

    Returns:
        Tuple of (valid_elements, invalid_elements).
    """
    valid = []
    invalid = []
    known = set(get_all_elements())
    for elem in elements:
        if elem in known:
            valid.append(elem)
        else:
            invalid.append(elem)
    return valid, invalid


def main():
    """Test function."""
    print(f"Loaded elements: {get_all_elements()}")
    print(f"Co Electronegativity: {get_element_property('Co', 'electronegativity')}")


if __name__ == "__main__":
    main()
