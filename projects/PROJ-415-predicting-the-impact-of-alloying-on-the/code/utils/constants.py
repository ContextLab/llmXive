from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ElementData:
    symbol: str
    metallic_radius: float
    electronegativity: float

# Simplified periodic table data for common FCC metals and solutes
# Radii in Angstroms, Electronegativity in Pauling scale
ELEMENT_DATABASE: Dict[str, ElementData] = {
    "Al": ElementData("Al", 1.43, 1.61),
    "Ag": ElementData("Ag", 1.44, 1.93),
    "Au": ElementData("Au", 1.44, 2.54),
    "Ca": ElementData("Ca", 1.97, 1.00),
    "Co": ElementData("Co", 1.25, 1.88),
    "Cu": ElementData("Cu", 1.28, 1.90),
    "Fe": ElementData("Fe", 1.24, 1.83),
    "Ga": ElementData("Ga", 1.35, 1.81),
    "Ir": ElementData("Ir", 1.36, 2.20),
    "Li": ElementData("Li", 1.52, 0.98),
    "Mg": ElementData("Mg", 1.60, 1.31),
    "Ni": ElementData("Ni", 1.25, 1.91),
    "Pb": ElementData("Pb", 1.75, 2.33),
    "Pd": ElementData("Pd", 1.37, 2.20),
    "Pt": ElementData("Pt", 1.39, 2.28),
    "Rh": ElementData("Rh", 1.34, 2.28),
    "Ru": ElementData("Ru", 1.34, 2.20),
    "Sr": ElementData("Sr", 2.15, 0.95),
    "Th": ElementData("Th", 1.80, 1.30),
    "Ti": ElementData("Ti", 1.47, 1.54),
    "V": ElementData("V", 1.34, 1.63),
    "Zn": ElementData("Zn", 1.33, 1.65),
    "Zr": ElementData("Zr", 1.60, 1.33),
}

def get_metallic_radius(symbol: str) -> Optional[float]:
    """Retrieve metallic radius for a given element symbol."""
    if symbol in ELEMENT_DATABASE:
        return ELEMENT_DATABASE[symbol].metallic_radius
    return None

def get_electronegativity(symbol: str) -> Optional[float]:
    """Retrieve electronegativity for a given element symbol."""
    if symbol in ELEMENT_DATABASE:
        return ELEMENT_DATABASE[symbol].electronegativity
    return None
