"""
Material Database Module for Nanowire Network Thermal Conductivity Simulations.

Provides access to bulk thermal conductivity values for standard materials
with NIST-derived defaults and validation logic.
"""

# NIST-derived default thermal conductivity values in W/(m·K)
# Source: NIST Reference on Constants, Units, and Uncertainty
NIST_DEFAULTS = {
    "Si": 149.0,
    "CNT": 3500.0,
    "Ag": 429.0,
    "Au": 318.0,
}

def get_material_conductivity(material_name: str) -> float:
    """
    Retrieve the bulk thermal conductivity for a given material.

    Args:
        material_name: Name of the material (e.g., "Si", "CNT", "Ag", "Au").

    Returns:
        Thermal conductivity value in W/(m·K).

    Raises:
        ValueError: If the material is not found in the local store or NIST defaults.
    """
    if material_name in NIST_DEFAULTS:
        return NIST_DEFAULTS[material_name]

    raise ValueError(
        f"Material {material_name} not found in local store or NIST defaults; "
        "please provide value in W/(m·K)."
    )

def list_available_materials() -> list:
    """
    List all materials available in the database.

    Returns:
        List of material names.
    """
    return list(NIST_DEFAULTS.keys())