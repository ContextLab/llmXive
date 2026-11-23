"""
Material constants and lattice parameter utilities for 2D materials.

This module provides access to material-specific constants, including lattice
parameters, which are read dynamically from the project configuration (config.yaml).
This ensures that critical values like R_lattice are not hardcoded but sourced
from the verified literature values stored in the configuration.
"""
from typing import Dict, Any, List, Optional
from src.config import get_config, ConfigError


# Base dictionary for known materials.
# Note: 'lattice' for graphene is a fixed structural constant (0.246 nm).
# The 'R_lattice' (resistance or effective lattice parameter for correction)
# is injected dynamically from config.yaml to satisfy T005 requirements.
_MATERIAL_BASE: Dict[str, Dict[str, Any]] = {
    "graphene": {
        "lattice": 0.246,  # nm, standard graphene lattice constant
        "description": "Single layer of carbon atoms in a hexagonal lattice"
    },
    "MoS2": {
        "lattice": 0.316,  # nm, approximate lattice constant for Molybdenum Disulfide
        "description": "Molybdenum Disulfide (Molybdenumite)"
    },
    "hBN": {
        "lattice": 0.250,  # nm, Hexagonal Boron Nitride
        "description": "Hexagonal Boron Nitride"
    }
}


def get_r_lattice() -> float:
    """
    Retrieves the R_lattice value from config.yaml.

    This value is critical for the background lattice correction (T025b) and
    must be set in config.yaml by T005 (from literature DOI: 10.1103/PhysRevB.93.045417).

    Returns:
        float: The verified R_lattice value.

    Raises:
        ConfigError: If 'R_lattice' is missing from config.yaml or cannot be parsed.
    """
    try:
        config = get_config()
        if "R_lattice" not in config:
            raise ConfigError(
                "R_lattice is missing from config.yaml. "
                "Please ensure T005 has populated this value from the literature source."
            )
        val = config["R_lattice"]
        if val is None:
            raise ConfigError("R_lattice in config.yaml is null.")
        return float(val)
    except KeyError as e:
        raise ConfigError(f"Configuration key error while fetching R_lattice: {e}")
    except ValueError as e:
        raise ConfigError(f"R_lattice value in config.yaml is not a valid number: {e}")


def get_material_constants(material_name: str) -> Dict[str, Any]:
    """
    Retrieves the full constant dictionary for a specific material.

    If the material is 'graphene', this function injects the 'R_lattice' value
    from the configuration into the returned dictionary to ensure consistency
    with the lattice correction requirements.

    Args:
        material_name (str): The name of the material (e.g., 'graphene', 'MoS2').

    Returns:
        Dict[str, Any]: A dictionary containing material constants.

    Raises:
        KeyError: If the material is not found in the base dictionary.
        ConfigError: If R_lattice is required but missing from config.
    """
    if material_name not in _MATERIAL_BASE:
        raise KeyError(f"Material '{material_name}' not found in MATERIAL_CONSTANTS.")

    # Deep copy to avoid mutating the base dictionary
    constants = _MATERIAL_BASE[material_name].copy()

    # Special handling for graphene to inject R_lattice from config
    # This satisfies the requirement to read R_lattice at runtime, not hardcode it.
    if material_name == "graphene":
        try:
            constants["R_lattice"] = get_r_lattice()
        except ConfigError as e:
            # Re-raise with context about the specific material
            raise ConfigError(
                f"Failed to load R_lattice for '{material_name}': {e}"
            ) from e

    return constants


def get_lattice_constant(material_name: str) -> float:
    """
    Retrieves the standard lattice constant (nm) for a given material.

    Args:
        material_name (str): The name of the material.

    Returns:
        float: The lattice constant in nanometers.

    Raises:
        KeyError: If the material is not found.
    """
    constants = get_material_constants(material_name)
    if "lattice" not in constants:
        raise KeyError(f"Material '{material_name}' does not have a defined lattice constant.")
    return float(constants["lattice"])


def list_available_materials() -> List[str]:
    """
    Returns a list of all available material names.

    Returns:
        List[str]: List of material keys.
    """
    return list(_MATERIAL_BASE.keys())


# Backward compatibility alias for the dictionary structure
MATERIAL_CONSTANTS = _MATERIAL_BASE