"""
Utilities for accessing material‑specific constants such as lattice constants.
The original implementation attempted to treat the configuration object as an
iterable, causing a TypeError. This rewritten module provides a clean, testable
API that works with the project's `src.config` module.
"""

from typing import Dict, List

from src.config import get_config, ConfigError

# Default material lattice constants (nm)
_DEFAULT_LATTICE_CONSTANTS: Dict[str, float] = {
    "graphene": 0.246,
    "mos2": 0.316,
    "default": 0.250,
}

def get_r_lattice() -> float:
    """
    Retrieve the `R_lattice` value from the global configuration.

    Returns:
        float: The R_lattice value.

    Raises:
        ConfigError: If the configuration does not contain `R_lattice`.
    """
    cfg = get_config()
    # `cfg` is a Config object; access attributes via dict‑style get if supported,
    # otherwise fallback to attribute access.
    try:
        # Some Config implementations support dict‑like access.
        value = cfg.get("R_lattice")  # type: ignore[attr-defined]
    except AttributeError:
        # Fallback to attribute access.
        value = getattr(cfg, "R_lattice", None)

    if value is None:
        raise ConfigError("Missing required configuration key: 'R_lattice'")
    return float(value)

def get_material_constants(material_name: str) -> Dict[str, float]:
    """
    Retrieve a dictionary of constants for the specified material.

    Args:
        material_name (str): Name of the material (e.g., 'graphene', 'MoS2').

    Returns:
        Dict[str, float]: Mapping of constant names to values.

    Raises:
        KeyError: If the material is unknown.
        ConfigError: If required configuration values are missing.
    """
    key = material_name.lower()
    if key not in _DEFAULT_LATTICE_CONSTANTS:
        raise KeyError(f"Material '{material_name}' not recognized.")
    lattice = _DEFAULT_LATTICE_CONSTANTS[key]

    # Example of injecting the R_lattice from config for graphene.
    if key == "graphene":
        r_lattice = get_r_lattice()
        return {"lattice_constant_nm": lattice, "R_lattice": r_lattice}
    else:
        return {"lattice_constant_nm": lattice}

def get_lattice_constant(material_name: str) -> float:
    """
    Retrieve the standard lattice constant (nm) for a given material.

    Args:
        material_name (str): The material name.

    Returns:
        float: Lattice constant in nanometers.

    Raises:
        KeyError: If the material is not found.
    """
    key = material_name.lower()
    if key not in _DEFAULT_LATTICE_CONSTANTS:
        raise KeyError(f"Material '{material_name}' not found.")
    return _DEFAULT_LATTICE_CONSTANTS[key]

def list_available_materials() -> List[str]:
    """
    Returns a list of all available material names.

    Returns:
        List[str]: Material identifiers.
    """
    return list(_DEFAULT_LATTICE_CONSTANTS.keys())
