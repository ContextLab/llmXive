import logging
from typing import Dict, Optional, Any, Union, List

logger = logging.getLogger(__name__)

# NIST Default Thermal Conductivities (W/(m·K))
NIST_DEFAULTS: Dict[str, float] = {
    "Si": 149.0,
    "CNT": 3500.0,
    "Ag": 429.0,
    "Au": 318.0
}

def get_material_conductivity(
    material_name: Union[str, Any], 
    bulk_conductivity: Optional[float] = None
) -> float:
    """
    Get thermal conductivity for a material.
    
    Supports three call patterns:
    1. get_material_conductivity(material_name) -> looks up NIST or raises
    2. get_material_conductivity(material_name, bulk_conductivity) -> uses provided value
    3. get_material_conductivity(config_obj) -> extracts material name and optional bulk_conductivity
    
    Args:
        material_name: String name, or object with .material attribute
        bulk_conductivity: Optional override value
        
    Returns:
        Thermal conductivity in W/(m·K)
        
    Raises:
        ValueError: If material not found and no override provided
    """
    # Handle config object case
    if hasattr(material_name, 'material'):
        # It's a config object
        name = material_name.material
        override = getattr(material_name, 'bulk_conductivity', None)
        if bulk_conductivity is None and override is not None:
            bulk_conductivity = override
    elif isinstance(material_name, str):
        name = material_name
    else:
        raise ValueError(f"Invalid material argument type: {type(material_name)}")
    
    # If override provided, use it
    if bulk_conductivity is not None:
        logger.debug(f"Using provided conductivity {bulk_conductivity} for {name}")
        return float(bulk_conductivity)
    
    # Look up in NIST
    if name in NIST_DEFAULTS:
        val = NIST_DEFAULTS[name]
        logger.debug(f"Using NIST default {val} for {name}")
        return val
    
    # Not found
    raise ValueError(f"Material {name} not found in local store or NIST defaults; please provide value in W/(m·K).")

def list_available_materials() -> List[str]:
    """Return list of available material names."""
    return list(NIST_DEFAULTS.keys())