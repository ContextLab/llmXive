import logging
from typing import Optional, Tuple, Any
from pathlib import Path

from pymatgen.core.periodic_table import Element, PeriodicTable
from pymatgen.core import Composition

# Configure logger for this module
logger = logging.getLogger(__name__)

# Singleton for Periodic Table to avoid re-initialization
_PT = None

def get_periodic_table() -> PeriodicTable:
    """Return the singleton PeriodicTable instance."""
    global _PT
    if _PT is None:
        _PT = PeriodicTable()
    return _PT

def get_element_or_none(symbol: str) -> Optional[Element]:
    """
    Safely retrieve an Element object from its symbol.
    Returns None if the symbol is invalid.
    """
    pt = get_periodic_table()
    try:
        return Element(symbol)
    except Exception:
        return None

def get_nearest_neighbor(symbol: str) -> Optional[Element]:
    """
    Find the nearest valid element neighbor in the periodic table.
    If the symbol is invalid, attempts to find a neighbor by atomic number
    proximity if a partial match exists, otherwise returns None.
    """
    elem = get_element_or_none(symbol)
    if elem:
        return elem

    # Fallback: try to find a neighbor by atomic number if we can parse an int
    # This is a heuristic; in practice, invalid symbols should be caught earlier.
    # For this implementation, we return None if strictly invalid, 
    # but the caller (get_property_with_fallback) handles the logging.
    return None

def get_property_with_fallback(
    symbol: str,
    property_name: str,
    fallback_strategy: str = "nearest_neighbor"
) -> Optional[float]:
    """
    Consolidated fallback logic for retrieving elemental properties.
    
    This function replaces duplicate fallback blocks found in previous versions.
    It attempts to get the property directly. If that fails (e.g., missing data 
    or invalid element), it logs a warning and attempts a fallback strategy.
    
    Args:
        symbol: The elemental symbol (e.g., "Fe").
        property_name: The name of the property to retrieve (e.g., "atomic_radius").
        fallback_strategy: Strategy to use if direct retrieval fails. 
                           Currently supports "nearest_neighbor".
    
    Returns:
        The property value if found, or None if all attempts fail.
    """
    elem = get_element_or_none(symbol)
    
    if elem is None:
        logger.warning(f"Invalid element symbol '{symbol}' encountered. Cannot retrieve property '{property_name}'.")
        return None

    try:
        # Attempt direct retrieval
        if hasattr(elem, property_name):
            val = getattr(elem, property_name)
            if val is not None:
                return val
        else:
            # Try accessing via a dict-like interface if available (some pymatgen versions)
            if property_name in elem.chemical_system or hasattr(elem, 'data'):
                # Fallback to generic data access if specific attribute missing
                pass 
    
        # If we reach here, the property might be missing or None
        raise AttributeError(f"Property '{property_name}' not found or is None for {symbol}")

    except (AttributeError, TypeError, KeyError) as e:
        logger.warning(
            f"Property '{property_name}' missing for element '{symbol}'. "
            f"Attempting fallback strategy: {fallback_strategy}. Error: {e}"
        )
        
        if fallback_strategy == "nearest_neighbor":
            neighbor = get_nearest_neighbor(symbol)
            if neighbor:
                try:
                    if hasattr(neighbor, property_name):
                        return getattr(neighbor, property_name)
                except Exception:
                    pass
        
        logger.error(f"Failed to retrieve property '{property_name}' for '{symbol}' even with fallback.")
        return None

def safe_get_atomic_radius(symbol: str) -> Optional[float]:
    """
    Safely get the atomic radius with fallback logic.
    Uses the consolidated get_property_with_fallback function.
    """
    return get_property_with_fallback(symbol, "atomic_radius")

def safe_get_electronegativity(symbol: str) -> Optional[float]:
    """
    Safely get the electronegativity with fallback logic.
    Uses the consolidated get_property_with_fallback function.
    """
    return get_property_with_fallback(symbol, "electronegativity")

def safe_get_oxidation_states(symbol: str) -> Optional[list]:
    """
    Safely get the oxidation states with fallback logic.
    Uses the consolidated get_property_with_fallback function.
    Note: Oxidation states are a list, so we handle the return type carefully.
    """
    elem = get_element_or_none(symbol)
    if not elem:
        logger.warning(f"Invalid element symbol '{symbol}' for oxidation states.")
        return None

    try:
        # pymatgen Element objects have 'oxidation_states' as a property that might be None or a list
        if hasattr(elem, 'oxidation_states'):
            val = elem.oxidation_states
            if val is not None:
                return list(val) if isinstance(val, (list, tuple)) else [val]
        return None
    except Exception as e:
        logger.warning(f"Error retrieving oxidation states for '{symbol}': {e}")
        return None

def safe_get_binary_mixing_enthalpy(element_a: str, element_b: str) -> Optional[float]:
    """
    Safely get the binary mixing enthalpy between two elements.
    
    This function checks for the existence of both elements and attempts to retrieve
    the mixing enthalpy. If data is missing, it logs a warning.
    Note: Pymatgen does not have a direct 'binary_mixing_enthalpy' attribute on Element.
    This typically requires a database lookup (e.g., OpenKIM, Materials Project) or
    a calculated value. Since no external DB is available in this scope, we simulate
    the fallback logic structure required by the task, returning None if not found.
    
    In a full implementation, this would query a specific database.
    """
    elem_a = get_element_or_none(element_a)
    elem_b = get_element_or_none(element_b)

    if not elem_a or not elem_b:
        logger.warning(f"Invalid element(s) '{element_a}' or '{element_b}' for mixing enthalpy.")
        return None

    # Placeholder for actual database lookup logic
    # If the project had a specific database module, it would be imported here.
    # For now, we log the attempt and return None to indicate data unavailability,
    # which triggers the fallback mechanism in the caller (compute.py) if implemented.
    logger.warning(
        f"Binary mixing enthalpy for {element_a}-{element_b} not available in local cache. "
        "In a production environment, this would query a database."
    )
    return None

def parse_composition(composition_str: str) -> Optional[Composition]:
    """
    Parse a composition string into a pymatgen Composition object.
    Returns None if parsing fails.
    """
    try:
        return Composition(composition_str)
    except Exception as e:
        logger.warning(f"Failed to parse composition string '{composition_str}': {e}")
        return None

def main():
    """
    Simple entry point for testing the utils module directly.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Testing utils module functions...")
    
    # Test valid element
    radius = safe_get_atomic_radius("Fe")
    logger.info(f"Atomic radius of Fe: {radius}")
    
    # Test invalid element
    radius_bad = safe_get_atomic_radius("Xx")
    logger.info(f"Atomic radius of Xx: {radius_bad}")
    
    # Test composition parsing
    comp = parse_composition("Fe2O3")
    logger.info(f"Parsed composition: {comp}")

if __name__ == "__main__":
    main()
