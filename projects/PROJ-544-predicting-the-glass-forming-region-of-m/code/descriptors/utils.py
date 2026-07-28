"""
Utility functions for elemental property retrieval with fallback logic.

This module provides robust access to elemental properties from pymatgen,
implementing a fallback strategy to nearest periodic table neighbors when
data is missing.
"""
import logging
from typing import Optional, Tuple, Any
from pathlib import Path
from pymatgen.core.periodic_table import Element, PeriodicTable
from pymatgen.core import Composition

# Initialize logger for this module
logger = logging.getLogger(__name__)
fallback_logger = logging.getLogger("fallback")

# Ensure fallback logger has a handler if not configured
if not fallback_logger.handlers:
    fh = logging.FileHandler("logs/fallback.log")
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    fallback_logger.addHandler(fh)
    fallback_logger.setLevel(logging.WARNING)

# Global periodic table instance
PT = PeriodicTable()

def get_element_or_none(symbol: str) -> Optional[Element]:
    """
    Safely retrieve an Element object from a symbol string.
    
    Args:
        symbol: Chemical symbol (e.g., 'Fe', 'Cu')
        
    Returns:
        Element object if valid, None otherwise
    """
    try:
        return Element(symbol)
    except Exception:
        return None

def get_nearest_neighbor(symbol: str) -> Optional[Element]:
    """
    Find the nearest neighbor in the periodic table for a given symbol.
    
    This function attempts to find a valid element by looking at adjacent
    atomic numbers when the original symbol is invalid or has missing properties.
    
    Args:
        symbol: The chemical symbol to find a neighbor for
        
    Returns:
        A valid Element object representing the nearest neighbor, or None if
        no valid neighbor can be found.
    """
    element = get_element_or_none(symbol)
    if element is None:
        # Try to parse as atomic number if symbol failed
        try:
            z = int(symbol)
            element = Element.from_Z(z)
        except (ValueError, TypeError):
            fallback_logger.warning(f"Invalid symbol/number '{symbol}' for nearest neighbor lookup.")
            return None
    
    atomic_number = element.Z
    pt = PT
    
    # Search neighbors by increasing distance
    for offset in range(1, 20):  # Limit search to reasonable distance
        # Check lower atomic number
        lower_z = atomic_number - offset
        if lower_z >= 1:
            try:
                neighbor = Element.from_Z(lower_z)
                if neighbor is not None:
                    fallback_logger.warning(
                        f"Nearest neighbor for '{symbol}' (Z={atomic_number}) is '{neighbor.symbol}' (Z={lower_z})"
                    )
                    return neighbor
            except Exception:
                pass
        
        # Check higher atomic number
        higher_z = atomic_number + offset
        try:
            # Max atomic number in pymatgen is around 118
            if higher_z <= 118:
                neighbor = Element.from_Z(higher_z)
                if neighbor is not None:
                    fallback_logger.warning(
                        f"Nearest neighbor for '{symbol}' (Z={atomic_number}) is '{neighbor.symbol}' (Z={higher_z})"
                    )
                    return neighbor
        except Exception:
            pass
    
    fallback_logger.error(f"Could not find a valid nearest neighbor for '{symbol}'")
    return None

def get_property_with_fallback(
    element: Element, 
    property_name: str, 
    default: Any = None
) -> Any:
    """
    Retrieve a property from an element, with fallback to nearest neighbor if missing.
    
    Args:
        element: The Element object to query
        property_name: Name of the property to retrieve (e.g., 'atomic_radius', 'electronegativity')
        default: Default value to return if no valid property is found
        
    Returns:
        The property value, or the default if not found
    """
    try:
        value = getattr(element, property_name)
        if value is not None and not (isinstance(value, float) and (value != value)):  # Check for NaN
            return value
    except AttributeError:
        pass
    
    # Property missing or invalid, try nearest neighbor
    neighbor = get_nearest_neighbor(element.symbol)
    if neighbor:
        try:
            value = getattr(neighbor, property_name)
            if value is not None and not (isinstance(value, float) and (value != value)):
                fallback_logger.warning(
                    f"Using '{property_name}'={value} from nearest neighbor '{neighbor.symbol}' "
                    f"since '{element.symbol}' is missing this property."
                )
                return value
        except AttributeError:
            pass
    
    fallback_logger.warning(
        f"Property '{property_name}' not found for '{element.symbol}' or its neighbors. "
        f"Using default value: {default}"
    )
    return default

def safe_get_atomic_radius(symbol: str) -> Optional[float]:
    """
    Safely get the atomic radius for an element, using fallback if necessary.
    
    Args:
        symbol: Chemical symbol
        
    Returns:
        Atomic radius in Angstroms, or None if not available
    """
    element = get_element_or_none(symbol)
    if element is None:
        fallback_logger.warning(f"Invalid element symbol '{symbol}' for atomic radius lookup.")
        return None
    
    # Try standard atomic radius first
    try:
        radius = element.atomic_radius
        if radius is not None and radius > 0:
            return float(radius)
    except Exception:
        pass
    
    # Try covalent radius if atomic radius is missing
    try:
        radius = element.covalent_radius
        if radius is not None and radius > 0:
            fallback_logger.warning(
                f"Using covalent radius {radius} for '{symbol}' as atomic radius is missing."
            )
            return float(radius)
    except Exception:
        pass
    
    # Fallback to nearest neighbor
    neighbor = get_nearest_neighbor(symbol)
    if neighbor:
        try:
            radius = neighbor.atomic_radius or neighbor.covalent_radius
            if radius is not None and radius > 0:
                fallback_logger.warning(
                    f"Using atomic radius {radius} from nearest neighbor '{neighbor.symbol}' for '{symbol}'."
                )
                return float(radius)
        except Exception:
            pass
    
    fallback_logger.error(f"Could not determine atomic radius for '{symbol}'.")
    return None

def safe_get_electronegativity(symbol: str) -> Optional[float]:
    """
    Safely get the electronegativity for an element, using fallback if necessary.
    
    Args:
        symbol: Chemical symbol
        
    Returns:
        Pauling electronegativity, or None if not available
    """
    element = get_element_or_none(symbol)
    if element is None:
        fallback_logger.warning(f"Invalid element symbol '{symbol}' for electronegativity lookup.")
        return None
    
    try:
        en = element.electronegativity
        if en is not None and en > 0:
            return float(en)
    except Exception:
        pass
    
    # Fallback to nearest neighbor
    neighbor = get_nearest_neighbor(symbol)
    if neighbor:
        try:
            en = neighbor.electronegativity
            if en is not None and en > 0:
                fallback_logger.warning(
                    f"Using electronegativity {en} from nearest neighbor '{neighbor.symbol}' for '{symbol}'."
                )
                return float(en)
        except Exception:
            pass
    
    fallback_logger.error(f"Could not determine electronegativity for '{symbol}'.")
    return None

def safe_get_oxidation_states(symbol: str) -> Optional[list]:
    """
    Safely get the common oxidation states for an element.
    
    Args:
        symbol: Chemical symbol
        
    Returns:
        List of common oxidation states, or None if not available
    """
    element = get_element_or_none(symbol)
    if element is None:
        fallback_logger.warning(f"Invalid element symbol '{symbol}' for oxidation states lookup.")
        return None
    
    try:
        states = element.oxidation_states
        if states:
            return list(states)
    except Exception:
        pass
    
    # Fallback to nearest neighbor
    neighbor = get_nearest_neighbor(symbol)
    if neighbor:
        try:
            states = neighbor.oxidation_states
            if states:
                fallback_logger.warning(
                    f"Using oxidation states {states} from nearest neighbor '{neighbor.symbol}' for '{symbol}'."
                )
                return list(states)
        except Exception:
            pass
    
    fallback_logger.warning(f"Could not determine oxidation states for '{symbol}'. Returning empty list.")
    return []

def safe_get_binary_mixing_enthalpy(element_a: str, element_b: str) -> Optional[float]:
    """
    Safely get the binary mixing enthalpy for an element pair.
    
    Note: pymatgen does not have a direct built-in for binary mixing enthalpy
    for all pairs. This function attempts to retrieve it from available data
    or returns None if not found.
    
    Args:
        element_a: First element symbol
        element_b: Second element symbol
        
    Returns:
        Mixing enthalpy in kJ/mol, or None if not available
    """
    el_a = get_element_or_none(element_a)
    el_b = get_element_or_none(element_b)
    
    if el_a is None or el_b is None:
        fallback_logger.warning(f"Invalid element pair ('{element_a}', '{element_b}') for mixing enthalpy.")
        return None
    
    # pymatgen doesn't have a direct binary mixing enthalpy table for all pairs.
    # We might need to use a database or approximate. For now, we return None
    # and log the fallback attempt.
    fallback_logger.warning(
        f"Binary mixing enthalpy for {element_a}-{element_b} not available in standard pymatgen data."
    )
    
    # Attempt fallback to nearest neighbors if one element is problematic
    # (though the primary issue is likely lack of data in pymatgen itself)
    if el_a is None:
        el_a = get_nearest_neighbor(element_a)
    if el_b is None:
        el_b = get_nearest_neighbor(element_b)
        
    if el_a and el_b:
        fallback_logger.warning(
            f"Attempting fallback mixing enthalpy for {el_a.symbol}-{el_b.symbol} (nearest neighbors)."
        )
        # In a real implementation, we would query a specific database here.
        # For now, we maintain the behavior of returning None if data is missing.
    
    return None

def parse_composition(composition_str: str) -> Optional[Composition]:
    """
    Safely parse a composition string into a pymatgen Composition object.
    
    Args:
        composition_str: String representation of composition (e.g., 'Cu50Zr50')
        
    Returns:
        Composition object, or None if parsing fails
    """
    try:
        return Composition(composition_str)
    except Exception as e:
        fallback_logger.error(f"Failed to parse composition '{composition_str}': {e}")
        return None

def main():
    """
    Main entry point for testing fallback logic.
    This function is primarily for demonstration and testing purposes.
    """
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        ("Fe", "atomic_radius"),
        ("Cu", "electronegativity"),
        ("Xe", "atomic_radius"),  # Noble gases might have missing data
        ("InvalidSymbol", "atomic_radius"),
        ("Fe", "oxidation_states"),
    ]
    
    for symbol, prop in test_cases:
        print(f"\nTesting {prop} for {symbol}:")
        if prop == "atomic_radius":
            result = safe_get_atomic_radius(symbol)
        elif prop == "electronegativity":
            result = safe_get_electronegativity(symbol)
        elif prop == "oxidation_states":
            result = safe_get_oxidation_states(symbol)
        else:
            result = None
        print(f"  Result: {result}")

if __name__ == "__main__":
    main()