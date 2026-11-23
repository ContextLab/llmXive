"""
Element configuration module.

This module provides functions to access the list of abundant elements
defined in the project configuration.
"""
from pathlib import Path
from typing import List, Set
import yaml

def _load_elements_config() -> List[str]:
    """Loads the abundant elements list from the YAML config file."""
    config_path = Path(__file__).parent.parent.parent / "data" / "config" / "elements.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config["abundant_elements"]

def get_abundant_elements() -> List[str]:
    """
    Returns the list of abundant elements.
    
    Returns:
        List of element symbols.
    """
    return _load_elements_config()

def get_abundant_elements_set() -> Set[str]:
    """
    Returns a set of abundant elements for fast lookup.
    
    Returns:
        Set of element symbols.
    """
    return set(get_abundant_elements())

def is_abundant_element(element: str) -> bool:
    """
    Checks if an element is in the abundant elements list.
    
    Args:
        element: Element symbol to check.
        
    Returns:
        True if the element is abundant, False otherwise.
    """
    return element in get_abundant_elements_set()

def main():
    """Main entry point for standalone execution (for testing)."""
    elements = get_abundant_elements()
    print(f"Abundant elements ({len(elements)}):")
    for i, elem in enumerate(elements, 1):
        print(f"  {i:2d}. {elem}")
    print(f"\nSet lookup test:")
    print(f"  Is Cu abundant? {is_abundant_element('Cu')}")
    print(f"  Is Au abundant? {is_abundant_element('Au')}")
    print(f"  Is U abundant? {is_abundant_element('U')}")

if __name__ == "__main__":
    main()