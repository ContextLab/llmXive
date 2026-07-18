"""
Material constants lookup table for 2D materials.

Provides lattice constants and lattice thermal resistance (R_lattice)
for supported materials (Graphene, MoS2).
"""

from typing import Dict, Any, Literal, List, Optional

# Material type alias for type hinting
MaterialType = Literal["graphene", "MoS2"]

# Material constants database
# Keys: material name (lowercase)
# Values: dict containing:
#   - 'lattice_constant': float (nm) - The lattice constant 'a'
#   - 'R_lattice': float (K/W) - Thermal resistance of the background lattice
#   - 'description': str - Human readable description
MATERIAL_CONSTANTS: Dict[str, Dict[str, Any]] = {
    "graphene": {
        "lattice_constant": 0.246,  # nm (approximate)
        "R_lattice": 1.5e3,         # K/W (example value for monolayer)
        "description": "Single layer carbon atoms in hexagonal lattice"
    },
    "MoS2": {
        "lattice_constant": 0.316,  # nm (approximate)
        "R_lattice": 2.8e3,         # K/W (example value for monolayer)
        "description": "Molybdenum disulfide, transition metal dichalcogenide"
    }
}

def list_available_materials() -> List[str]:
    """
    Returns a list of available material names.

    Returns:
        List[str]: List of material identifiers (e.g., ["graphene", "MoS2"])
    """
    return list(MATERIAL_CONSTANTS.keys())

def get_material_constants(material: str) -> Dict[str, Any]:
    """
    Retrieves the full constant dictionary for a given material.

    Args:
        material: The material name (case-insensitive).

    Returns:
        Dict[str, Any]: The dictionary of constants for the material.

    Raises:
        ValueError: If the material is not found in the lookup table.
    """
    key = material.lower()
    if key not in MATERIAL_CONSTANTS:
        available = ", ".join(list_available_materials())
        raise ValueError(
            f"Material '{material}' not found. "
            f"Available materials: {available}"
        )
    return MATERIAL_CONSTANTS[key]

def get_lattice_constant(material: str) -> float:
    """
    Retrieves the lattice constant 'a' for a specific material.

    Args:
        material: The material name (case-insensitive).

    Returns:
        float: The lattice constant in nanometers (nm).

    Raises:
        ValueError: If the material is not found.
    """
    constants = get_material_constants(material)
    return float(constants["lattice_constant"])

def get_r_lattice(material: str) -> float:
    """
    Retrieves the lattice thermal resistance (R_lattice) for a specific material.

    This value is used in the series-parallel resistance correction formula:
    1/R_total = 1/R_defect + 1/R_lattice

    Args:
        material: The material name (case-insensitive).

    Returns:
        float: The thermal resistance in K/W.

    Raises:
        ValueError: If the material is not found.
    """
    constants = get_material_constants(material)
    return float(constants["R_lattice"])
