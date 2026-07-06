"""
Wrapper for mendeleev periodic table lookups.

Provides utility functions to retrieve elemental properties (atomic radius,
electronegativity, valence electron count, atomic number) from the mendeleev
database, with caching and error handling for missing elements.
"""

from functools import lru_cache
from typing import Dict, Optional, Union

from mendeleev import element as mendeleev_element
from mendeleev.exceptions import NotFoundError


@lru_cache(maxsize=128)
def get_element(symbol: str):
    """
    Retrieve an Element object from mendeleev by symbol.

    Args:
        symbol: Chemical symbol (e.g., 'Bi', 'Te', 'Pb').

    Returns:
        mendeleev.element.Element object.

    Raises:
        ValueError: If the symbol is invalid or element not found.
    """
    try:
        return mendeleev_element(symbol)
    except NotFoundError:
        raise ValueError(f"Element not found for symbol: '{symbol}'")


@lru_cache(maxsize=128)
def get_atomic_radius(symbol: str) -> Optional[float]:
    """
    Get the atomic radius (empirical) for an element.

    Args:
        symbol: Chemical symbol.

    Returns:
        Atomic radius in picometers (pm), or None if not available.
    """
    try:
        elem = get_element(symbol)
        # Prefer empirical atomic radius; fallback to covalent if needed
        if elem.atomic_radius is not None:
            return float(elem.atomic_radius)
        if elem.covalent_radius is not None:
            return float(elem.covalent_radius)
        return None
    except ValueError:
        return None


@lru_cache(maxsize=128)
def get_electronegativity(symbol: str) -> Optional[float]:
    """
    Get the Pauling electronegativity for an element.

    Args:
        symbol: Chemical symbol.

    Returns:
        Electronegativity value, or None if not available.
    """
    try:
        elem = get_element(symbol)
        if elem.electronegativity is not None:
            return float(elem.electronegativity)
        return None
    except ValueError:
        return None


@lru_cache(maxsize=128)
def get_valence_electrons(symbol: str) -> Optional[int]:
    """
    Get the number of valence electrons for an element.

    Args:
        symbol: Chemical symbol.

    Returns:
        Number of valence electrons, or None if not available.
    """
    try:
        elem = get_element(symbol)
        # Mendeleev stores valence electrons as a list; we take the max or first non-null
        if elem.valence_electrons:
            # valence_electrons returns a list of possible valences
            # For feature engineering, we typically use the group number or max valence
            # Mendeleev's 'group' property is more reliable for VEC in alloys
            return elem.group
        # Fallback to group number if valence_electrons is empty
        return elem.group
    except ValueError:
        return None


@lru_cache(maxsize=128)
def get_atomic_number(symbol: str) -> Optional[int]:
    """
    Get the atomic number for an element.

    Args:
        symbol: Chemical symbol.

    Returns:
        Atomic number (Z), or None if not available.
    """
    try:
        elem = get_element(symbol)
        return int(elem.atomic_number)
    except ValueError:
        return None


def get_element_properties(symbol: str) -> Dict[str, Union[float, int, None]]:
    """
    Retrieve a dictionary of key properties for an element.

    Args:
        symbol: Chemical symbol.

    Returns:
        Dictionary with keys: 'atomic_radius', 'electronegativity',
        'valence_electrons', 'atomic_number'.
    """
    return {
        "atomic_radius": get_atomic_radius(symbol),
        "electronegativity": get_electronegativity(symbol),
        "valence_electrons": get_valence_electrons(symbol),
        "atomic_number": get_atomic_number(symbol),
    }