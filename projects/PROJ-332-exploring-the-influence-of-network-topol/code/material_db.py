import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# NIST default thermal conductivities in W/(m·K)
NIST_DEFAULTS = {
    'Si': 149.0,
    'CNT': 3500.0,
    'Ag': 429.0,
    'Au': 318.0
}

def get_material_conductivity(material: str) -> float:
    """
    Get thermal conductivity for a material.
    Raises ValueError if material not found.
    """
    material_upper = material.upper()
    
    if material_upper in NIST_DEFAULTS:
        return NIST_DEFAULTS[material_upper]
    
    # Check if it's a known material in lowercase
    if material in NIST_DEFAULTS:
        return NIST_DEFAULTS[material]
    
    error_msg = f"Material {material} not found in local store or NIST defaults; please provide value in W/(m·K)."
    logger.error(error_msg)
    raise ValueError(error_msg)

def list_available_materials() -> list:
    """List all available materials in the database."""
    return list(NIST_DEFAULTS.keys())
