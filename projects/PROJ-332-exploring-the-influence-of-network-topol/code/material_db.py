import logging
from typing import Dict, Optional, Any, Union

# NIST default thermal conductivities in W/(m·K)
NIST_DEFAULTS: Dict[str, float] = {
    "Si": 149.0,
    "CNT": 3500.0,
    "Ag": 429.0,
    "Au": 318.0,
}

logger = logging.getLogger(__name__)

def get_material_conductivity(
    material: str,
    provided_k: Optional[float] = None,
    **kwargs: Any
) -> float:
    """
    Retrieve thermal conductivity for a given material.

    Signature compatibility:
      1. get_material_conductivity(material)
      2. get_material_conductivity(material, provided_k)
      3. get_material_conductivity(material, provided_k, **kwargs)

    Logic:
      - If 'provided_k' is not None, use it (user override).
      - Else if material is in NIST_DEFAULTS, use the default.
      - Else raise a clear error.

    Args:
        material: Name of the material (e.g., "Si", "Ag").
        provided_k: Optional explicit conductivity value to use.

    Returns:
        Thermal conductivity in W/(m·K).

    Raises:
        ValueError: If material is not found and no value is provided.
    """
    if provided_k is not None:
        logger.debug(f"Using provided conductivity {provided_k} for {material}")
        return float(provided_k)

    if material in NIST_DEFAULTS:
        val = NIST_DEFAULTS[material]
        logger.debug(f"Using NIST default {val} for {material}")
        return val

    raise ValueError(
        f"Material {material} not found in local store or NIST defaults; "
        "please provide value in W/(m·K)."
    )

def list_available_materials() -> list:
    """Return a list of material names available in the NIST defaults."""
    return list(NIST_DEFAULTS.keys())
