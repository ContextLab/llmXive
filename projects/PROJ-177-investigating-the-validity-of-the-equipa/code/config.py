"""
Configuration loader for granular system analysis.
Loads material properties and frequency bins from data/config.yaml.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the configuration file from the specified path.

    Args:
        config_path: Path to the config YAML file. Defaults to 'data/config.yaml'.

    Returns:
        Dictionary containing the configuration data.

    Raises:
        ConfigError: If the file cannot be found or parsed.
    """
    if config_path is None:
        config_path = "data/config.yaml"

    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")

    if not isinstance(config, dict):
        raise ConfigError("Configuration file must contain a top-level dictionary.")

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the structure of the loaded configuration.

    Args:
        config: The configuration dictionary.

    Raises:
        ConfigError: If required keys are missing or malformed.
    """
    if "materials" not in config:
        raise ConfigError("Configuration must contain a 'materials' key.")

    if "frequency_bins" not in config:
        raise ConfigError("Configuration must contain a 'frequency_bins' key.")

    materials = config["materials"]
    if not isinstance(materials, dict):
        raise ConfigError("'materials' must be a dictionary.")

    for name, props in materials.items():
        if not isinstance(props, dict):
            raise ConfigError(f"Material '{name}' must be a dictionary.")
        required_props = ["mass", "inertia", "roughness_proxy"]
        for prop in required_props:
            if prop not in props:
                raise ConfigError(f"Material '{name}' missing required property: {prop}")
            if not isinstance(props[prop], (int, float)):
                raise ConfigError(f"Property '{prop}' for material '{name}' must be numeric.")

    frequency_bins = config["frequency_bins"]
    if not isinstance(frequency_bins, list):
        raise ConfigError("'frequency_bins' must be a list.")

    for i, bin_def in enumerate(frequency_bins):
        if not isinstance(bin_def, dict):
            raise ConfigError(f"Frequency bin {i} must be a dictionary.")
        required_bin_keys = ["label", "min_hz", "max_hz"]
        for key in required_bin_keys:
            if key not in bin_def:
                raise ConfigError(f"Frequency bin {i} missing required key: {key}")


def get_material_properties(config: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
    """
    Retrieve all material properties from the configuration.

    Args:
        config: Optional pre-loaded config dictionary. If None, loads from default path.

    Returns:
        Dictionary mapping material names to their properties (mass, inertia, roughness_proxy).
    """
    if config is None:
        config = load_config()

    validate_config(config)
    return config["materials"]


def get_frequency_bins(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Retrieve frequency bin definitions from the configuration.

    Args:
        config: Optional pre-loaded config dictionary. If None, loads from default path.

    Returns:
        List of dictionaries, each containing 'label', 'min_hz', and 'max_hz'.
    """
    if config is None:
        config = load_config()

    validate_config(config)
    return config["frequency_bins"]


def get_roughness_proxy(material_name: str, config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the roughness proxy for a specific material.

    Args:
        material_name: Name of the material (e.g., 'steel').
        config: Optional pre-loaded config dictionary.

    Returns:
        The roughness proxy value.

    Raises:
        ConfigError: If material is not found.
    """
    if config is None:
        config = load_config()

    materials = get_material_properties(config)
    if material_name not in materials:
        raise ConfigError(f"Material '{material_name}' not found in configuration.")

    return materials[material_name]["roughness_proxy"]


def get_mass(material_name: str, config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the mass for a specific material.

    Args:
        material_name: Name of the material.
        config: Optional pre-loaded config dictionary.

    Returns:
        The mass value in kg.

    Raises:
        ConfigError: If material is not found.
    """
    if config is None:
        config = load_config()

    materials = get_material_properties(config)
    if material_name not in materials:
        raise ConfigError(f"Material '{material_name}' not found in configuration.")

    return materials[material_name]["mass"]


def get_inertia(material_name: str, config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the moment of inertia for a specific material.

    Args:
        material_name: Name of the material.
        config: Optional pre-loaded config dictionary.

    Returns:
        The moment of inertia value in kg*m^2.

    Raises:
        ConfigError: If material is not found.
    """
    if config is None:
        config = load_config()

    materials = get_material_properties(config)
    if material_name not in materials:
        raise ConfigError(f"Material '{material_name}' not found in configuration.")

    return materials[material_name]["inertia"]


def main() -> None:
    """
    Main entry point for testing the configuration loader.
    Prints loaded materials and frequency bins to stdout.
    """
    try:
        config = load_config()
        print("Configuration loaded successfully.")
        print("\n--- Materials ---")
        materials = get_material_properties(config)
        for name, props in materials.items():
            print(f"  {name}:")
            print(f"    Mass: {props['mass']} kg")
            print(f"    Inertia: {props['inertia']} kg*m^2")
            print(f"    Roughness Proxy: {props['roughness_proxy']}")

        print("\n--- Frequency Bins ---")
        bins = get_frequency_bins(config)
        for bin_def in bins:
            print(f"  {bin_def['label']}: {bin_def['min_hz']} - {bin_def['max_hz']} Hz")

    except ConfigError as e:
        print(f"Configuration Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()