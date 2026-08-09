"""
Configuration loader for the granular system project.

Loads material properties and frequency bins from data/config.yaml.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the configuration file.
    
    Args:
        config_path: Optional path to config file. Defaults to data/config.yaml.
        
    Returns:
        Dictionary containing configuration data.
        
    Raises:
        ConfigError: If file not found or invalid YAML.
    """
    if config_path is None:
        config_path = Path("data") / "config.yaml"
    
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration structure.
    
    Args:
        config: Configuration dictionary to validate.
        
    Raises:
        ConfigError: If validation fails.
    """
    required_keys = ["materials", "frequency_bins", "constants"]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required config key: {key}")
    
    # Check for at least one material with required fields
    materials = config.get("materials", {})
    if not materials:
        raise ConfigError("No materials defined in config")
    
    for mat_name, mat_props in materials.items():
        if "mass_density" not in mat_props:
            raise ConfigError(f"Missing mass_density for material '{mat_name}'")
        if "roughness_proxy" not in mat_props:
            raise ConfigError(f"Missing roughness_proxy for material '{mat_name}'")
    
    # Validate frequency_bins structure
    freq_bins = config.get("frequency_bins", [])
    if not freq_bins:
        raise ConfigError("No frequency_bins defined in config")
    
    for i, bin_def in enumerate(freq_bins):
        if "name" not in bin_def:
            raise ConfigError(f"Missing 'name' in frequency_bins[{i}]")
        if "min_hz" not in bin_def or "max_hz" not in bin_def:
            raise ConfigError(f"Missing 'min_hz' or 'max_hz' in frequency_bins[{i}]")


def get_material_properties(config: Dict[str, Any], material_name: str) -> Dict[str, float]:
    """
    Get properties for a specific material.
    
    Args:
        config: Configuration dictionary.
        material_name: Name of the material (e.g., 'steel', 'polymer').
        
    Returns:
        Dictionary of material properties.
        
    Raises:
        ConfigError: If material not found.
    """
    if material_name not in config.get("materials", {}):
        raise ConfigError(f"Material '{material_name}' not found in config")
    
    return config["materials"][material_name]


def get_frequency_bins(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get frequency bin definitions.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        List of frequency bin definitions.
    """
    return config.get("frequency_bins", [])


def get_roughness_proxy(config: Dict[str, Any], material_name: str) -> float:
    """
    Get the roughness proxy for a material.
    
    Args:
        config: Configuration dictionary.
        material_name: Name of the material.
        
    Returns:
        Roughness proxy value.
        
    Raises:
        ConfigError: If material not found or missing roughness.
    """
    props = get_material_properties(config, material_name)
    if "roughness_proxy" not in props:
        raise ConfigError(f"Missing roughness_proxy for {material_name}")
    return props["roughness_proxy"]


def get_mass(config: Dict[str, Any], material_name: str) -> float:
    """
    Calculate mass of a particle given material and default radius.
    
    Formula: m = density * volume = density * (4/3 * pi * r^3)
    
    Args:
        config: Configuration dictionary.
        material_name: Name of the material.
        
    Returns:
        Mass in kg.
    """
    props = get_material_properties(config, material_name)
    density = props["mass_density"]
    radius = props.get("radius", 0.0025) # Default 2.5mm
    
    volume = (4.0 / 3.0) * 3.1415926535 * (radius ** 3)
    return density * volume


def get_inertia(config: Dict[str, Any], material_name: str) -> float:
    """
    Calculate moment of inertia for a solid sphere.
    
    Formula: I = (2/5) * m * r^2
    
    Args:
        config: Configuration dictionary.
        material_name: Name of the material.
        
    Returns:
        Moment of inertia in kg*m^2.
    """
    mass = get_mass(config, material_name)
    props = get_material_properties(config, material_name)
    radius = props.get("radius", 0.0025)
    
    # Factor from config or default 2/5 for solid sphere
    factor = config.get("constants", {}).get("moment_of_inertia_factor", 0.4)
    
    return factor * mass * (radius ** 2)

def main():
    """Simple test runner for config module."""
    try:
        config = load_config()
        validate_config(config)
        print("Config loaded and validated successfully.")
        print(f"Materials: {list(config['materials'].keys())}")
        print(f"Steel mass: {get_mass(config, 'steel'):.6f} kg")
        print(f"Steel inertia: {get_inertia(config, 'steel'):.6e} kg*m^2")
        
        # Print frequency bins
        bins = get_frequency_bins(config)
        print(f"Frequency bins: {len(bins)}")
        for b in bins:
            print(f"  - {b['name']}: {b['min_hz']}-{b['max_hz']} Hz")
            
        # Test roughness proxy
        for mat in config['materials'].keys():
            rp = get_roughness_proxy(config, mat)
            print(f"  Roughness ({mat}): {rp}")
            
    except ConfigError as e:
        print(f"Config Error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())