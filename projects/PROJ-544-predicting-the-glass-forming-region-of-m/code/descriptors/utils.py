"""
Utilities for descriptor computation.

This module provides functions for accessing elemental properties from pymatgen,
including fallback logic for missing data.

Refactored by T033: Consolidated duplicate fallback logic into a single
`get_fallback_property` function.
"""
import logging
from typing import Optional, Tuple, Any
from pathlib import Path
from pymatgen.core.periodic_table import Element, PeriodicTable
from pymatgen.core import Composition
import numpy as np

# Cache for the periodic table to avoid re-loading
_PERIODIC_TABLE: Optional[PeriodicTable] = None

def get_periodic_table() -> PeriodicTable:
    """Return the singleton PeriodicTable instance."""
    global _PERIODIC_TABLE
    if _PERIODIC_TABLE is None:
        _PERIODIC_TABLE = PeriodicTable()
    return _PERIODIC_TABLE

def get_element_or_none(symbol: str) -> Optional[Element]:
    """
    Get an Element object by symbol.
    
    Args:
        symbol: Elemental symbol (e.g., 'Cu', 'Zr').
        
    Returns:
        Element object or None if symbol is invalid.
    """
    try:
        return Element(symbol)
    except Exception:
        return None

def get_nearest_neighbor(symbol: str) -> Optional[Element]:
    """
    Find the nearest neighbor in the periodic table for a given symbol.
    
    This is used as a fallback when an element's property is missing.
    
    Args:
        symbol: Elemental symbol.
        
    Returns:
        Nearest neighbor Element or None if no valid element found.
    """
    elem = get_element_or_none(symbol)
    if elem is None:
        return None
    
    pt = get_periodic_table()
    current_group = elem.group
    current_period = elem.period
    
    # Search neighbors in order of proximity
    # Priority: same group (adjacent periods), same period (adjacent groups)
    candidates = []
    
    # Check adjacent periods in same group
    for period_offset in [-1, 1]:
        p = current_period + period_offset
        if 1 <= p <= 7:
            try:
                # Try to find element with same group in adjacent period
                # We need to iterate because group numbers don't map 1:1 to indices
                for el in pt:
                    if el.group == current_group and el.period == p:
                        candidates.append((abs(period_offset), 0, el))
                        break
            except Exception:
                continue
    
    # Check adjacent groups in same period
    for group_offset in [-1, 1]:
        g = current_group + group_offset
        if 1 <= g <= 18:
            try:
                el = pt.get_element_by_group_and_period(g, current_period)
                if el:
                    candidates.append((0, abs(group_offset), el))
            except Exception:
                continue
    
    if not candidates:
        return None
    
    # Sort by distance (period diff, group diff)
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]

def get_property_with_fallback(
    elem: Element, 
    prop_name: str, 
    fallback_func,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Get a property from an element, with fallback to nearest neighbor if missing.
    
    This is the consolidated fallback logic for all property lookups.
    
    Args:
        elem: The Element object to query.
        prop_name: Name of the property to retrieve (e.g., 'atomic_radius').
        fallback_func: A function that takes an Element and returns the property.
                       This should be the specific getter (e.g., safe_get_atomic_radius).
        logger: Optional logger for warnings.
                
    Returns:
        The property value, or the fallback value if the primary is missing.
    """
    try:
        # Try to get the property directly
        value = fallback_func(elem)
        if value is not None:
            return value
    except Exception:
        pass
    
    # Property missing, try nearest neighbor
    if logger:
        logger.warning(
            f"Property '{prop_name}' missing for {elem.symbol}. "
            f"Using nearest neighbor fallback."
        )
    
    neighbor = get_nearest_neighbor(elem.symbol)
    if neighbor is not None:
        try:
            fallback_value = fallback_func(neighbor)
            if fallback_value is not None:
                return fallback_value
        except Exception:
            pass
    
    # If all else fails, return None
    return None

def safe_get_atomic_radius(elem: Element) -> Optional[float]:
    """Safely get atomic radius, handling missing data."""
    try:
        # Try ionic radius first, then atomic radius
        if hasattr(elem, 'atomic_radius'):
            return elem.atomic_radius
        return None
    except Exception:
        return None

def safe_get_electronegativity(elem: Element) -> Optional[float]:
    """Safely get electronegativity (Pauling scale), handling missing data."""
    try:
        if hasattr(elem, 'electronegativity'):
            return elem.electronegativity
        return None
    except Exception:
        return None

def safe_get_oxidation_states(elem: Element) -> Optional[list]:
    """Safely get common oxidation states, handling missing data."""
    try:
        if hasattr(elem, 'oxidation_states'):
            return elem.oxidation_states
        return None
    except Exception:
        return None

def safe_get_binary_mixing_enthalpy(
    elem1: Element, 
    elem2: Element
) -> Optional[float]:
    """
    Safely get binary mixing enthalpy between two elements.
    
    Note: This is a placeholder. In a real implementation, this would query
    a database like the Miedema model or Materials Project.
    """
    # Placeholder: In a real system, this would query an external database
    # For now, return None to trigger fallback logic if needed
    return None

def parse_composition(composition_str: str) -> Optional[Composition]:
    """
    Parse a composition string into a pymatgen Composition object.
    
    Args:
        composition_str: String like 'Cu50Zr50' or 'Cu_0.5 Zr_0.5'.
        
    Returns:
        Composition object or None if parsing fails.
    """
    try:
        return Composition(composition_str)
    except Exception:
        return None

def main():
    """
    Main entry point for standalone execution.
    Runs a simple test of the fallback logic.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    pt = get_periodic_table()
    
    # Test with a known element
    cu = get_element_or_none("Cu")
    if cu:
        radius = safe_get_atomic_radius(cu)
        logger.info(f"Cu atomic radius: {radius}")
        
        # Test fallback with a hypothetical missing property
        # (In reality, Cu has a radius, so this demonstrates the logic)
        fallback_val = get_property_with_fallback(
            cu, 
            "atomic_radius", 
            safe_get_atomic_radius, 
            logger
        )
        logger.info(f"Cu radius with fallback: {fallback_val}")
    
    logger.info("Utility functions tested successfully.")

if __name__ == "__main__":
    main()
