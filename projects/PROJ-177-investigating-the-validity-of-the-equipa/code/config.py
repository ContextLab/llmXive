import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

def load_config(config_path: str = "data/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def validate_config(config: Dict[str, Any]) -> None:
    """Validate required fields in config."""
    required_fields = ['mass', 'radius', 'material_type', 'frequency_bins']
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ConfigError(f"Missing required config fields: {missing}")
    
    # Validate frequency_bins are strictly increasing
    freq_bins = config.get('frequency_bins', [])
    if freq_bins and not all(freq_bins[i] < freq_bins[i+1] for i in range(len(freq_bins)-1)):
        raise ConfigError("frequency_bins must be strictly increasing")

def get_material_properties(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract material properties from config."""
    return {
        'mass': config['mass'],
        'radius': config['radius'],
        'material_type': config['material_type']
    }

def get_frequency_bins(config: Dict[str, Any]) -> List[float]:
    """Extract frequency bins from config."""
    return config['frequency_bins']

def get_roughness_proxy(config: Dict[str, Any]) -> float:
    """Get roughness proxy (default to 0.1 if not specified)."""
    return config.get('roughness_proxy', 0.1)

def get_mass(config: Dict[str, Any]) -> float:
    """Get mass from config."""
    return config['mass']

def get_inertia(config: Dict[str, Any]) -> float:
    """Calculate moment of inertia for a sphere: I = (2/5) * m * r^2."""
    m = config['mass']
    r = config['radius']
    return (2.0 / 5.0) * m * r * r

def main():
    """CLI entry point for config validation."""
    import argparse
    parser = argparse.ArgumentParser(description='Validate configuration file')
    parser.add_argument('--config', default='data/config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        validate_config(config)
        print(f"Config validation successful: {args.config}")
        print(f"  Mass: {config['mass']} kg")
        print(f"  Radius: {config['radius']} m")
        print(f"  Material: {config['material_type']}")
        print(f"  Frequency bins: {config['frequency_bins']} Hz")
    except (FileNotFoundError, ConfigError) as e:
        print(f"Config validation failed: {e}")
        return 1
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
