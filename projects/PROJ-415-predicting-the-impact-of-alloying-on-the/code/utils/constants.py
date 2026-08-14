"""
Constants and utility functions for periodic table data.
"""

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ElementData:
    """Data class for element properties."""
    metallic_radius: float  # in Angstroms
    electronegativity: float
    atomic_number: int
    symbol: str

# Simplified periodic table data for testing and common elements
# In a real scenario, this would be a larger dataset or loaded from a file
PERIODIC_TABLE_DATA: Dict[str, ElementData] = {
    "Cu": ElementData(metallic_radius=1.28, electronegativity=1.90, atomic_number=29, symbol="Cu"),
    "Ni": ElementData(metallic_radius=1.24, electronegativity=1.91, atomic_number=28, symbol="Ni"),
    "Ag": ElementData(metallic_radius=1.44, electronegativity=1.93, atomic_number=47, symbol="Ag"),
    "Au": ElementData(metallic_radius=1.44, electronegativity=2.54, atomic_number=79, symbol="Au"),
    "Zn": ElementData(metallic_radius=1.33, electronegativity=1.65, atomic_number=30, symbol="Zn"),
    "Al": ElementData(metallic_radius=1.43, electronegativity=1.61, atomic_number=13, symbol="Al"),
    "Fe": ElementData(metallic_radius=1.26, electronegativity=1.83, atomic_number=26, symbol="Fe"),
    "Pb": ElementData(metallic_radius=1.75, electronegativity=2.33, atomic_number=82, symbol="Pb"),
    "Mg": ElementData(metallic_radius=1.60, electronegativity=1.31, atomic_number=12, symbol="Mg"),
    "Ca": ElementData(metallic_radius=1.97, electronegativity=1.00, atomic_number=20, symbol="Ca"),
}

def get_metallic_radius(element_symbol: str) -> Optional[float]:
    """
    Get the metallic radius for a given element symbol.
    
    Args:
        element_symbol: The chemical symbol of the element (e.g., 'Cu')
        
    Returns:
        The metallic radius in Angstroms, or None if the element is not found.
    """
    element_symbol = element_symbol.strip().capitalize()
    if element_symbol in PERIODIC_TABLE_DATA:
        return PERIODIC_TABLE_DATA[element_symbol].metallic_radius
    return None

def get_electronegativity(element_symbol: str) -> Optional[float]:
    """
    Get the electronegativity for a given element symbol.
    
    Args:
        element_symbol: The chemical symbol of the element (e.g., 'Cu')
        
    Returns:
        The electronegativity value, or None if the element is not found.
    """
    element_symbol = element_symbol.strip().capitalize()
    if element_symbol in PERIODIC_TABLE_DATA:
        return PERIODIC_TABLE_DATA[element_symbol].electronegativity
    return None
