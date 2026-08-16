from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ElementData:
    metallic_radius: Optional[float]  # in Angstroms
    electronegativity: Optional[float] # Pauling scale

# Simplified periodic table data for common FCC metals and solutes
# Source: Standard metallic radii tables (e.g., Kittel, Ashcroft & Mermin)
# Note: This is a subset. In a real production system, this would be a full database.
ELEMENT_DATA: Dict[str, ElementData] = {
    # Host Metals (FCC)
    "Cu": ElementData(metallic_radius=1.28, electronegativity=1.90),
    "Al": ElementData(metallic_radius=1.43, electronegativity=1.61),
    "Ni": ElementData(metallic_radius=1.24, electronegativity=1.91),
    "Ag": ElementData(metallic_radius=1.44, electronegativity=1.93),
    "Au": ElementData(metallic_radius=1.44, electronegativity=2.54),
    "Pt": ElementData(metallic_radius=1.39, electronegativity=2.28),
    "Pd": ElementData(metallic_radius=1.37, electronegativity=2.20),
    "Pb": ElementData(metallic_radius=1.75, electronegativity=2.33),
    "Ca": ElementData(metallic_radius=1.97, electronegativity=1.00),
    
    # Common Solutes
    "Zn": ElementData(metallic_radius=1.33, electronegativity=1.65),
    "Mg": ElementData(metallic_radius=1.60, electronegativity=1.31),
    "Fe": ElementData(metallic_radius=1.24, electronegativity=1.83), # BCC usually, but can be FCC in alloys
    "Cr": ElementData(metallic_radius=1.28, electronegativity=1.66),
    "Mn": ElementData(metallic_radius=1.27, electronegativity=1.55),
    "Si": ElementData(metallic_radius=1.17, electronegativity=1.90),
    "Ti": ElementData(metallic_radius=1.47, electronegativity=1.54),
    "V": ElementData(metallic_radius=1.34, electronegativity=1.63),
    "Nb": ElementData(metallic_radius=1.46, electronegativity=1.60),
    "Ta": ElementData(metallic_radius=1.46, electronegativity=1.50),
    "Mo": ElementData(metallic_radius=1.39, electronegativity=2.16),
    "W": ElementData(metallic_radius=1.39, electronegativity=2.36),
}

def get_metallic_radius(element: str) -> Optional[float]:
    """
    Retrieve the metallic radius for a given element symbol.
    Returns None if the element is not found in the database.
    """
    element = element.strip().title() # Normalize case
    data = ELEMENT_DATA.get(element)
    if data:
        return data.metallic_radius
    return None

def get_electronegativity(element: str) -> Optional[float]:
    """
    Retrieve the electronegativity for a given element symbol.
    """
    element = element.strip().title()
    data = ELEMENT_DATA.get(element)
    if data:
        return data.electronegativity
    return None
