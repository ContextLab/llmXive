"""
Configuration management module for the Network Topology Heat Dissipation project.

This module handles loading, validating, and accessing configuration parameters
from the config.yaml file. It provides a centralized source of truth for all
simulation and analysis parameters.
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

# Default configuration values
DEFAULT_CONFIG = {
    "project": {
        "name": "network-topology-heat-dissipation",
        "version": "1.0.0",
        "seed": 42
    },
    "simulation": {
        "distance_threshold_nm": 2.0,
        "statistical_override": False,
        "threshold_multiplier": 1.5
    },
    "materials": {
        "graphene": {
            "lattice_constant_nm": 0.246,
            "r_lattice": 1000.0
        },
        "mos2": {
            "lattice_constant_nm": 0.316,
            "r_lattice": 150.0
        }
    },
    "analysis": {
        "bootstrap_ci": 0.95,
        "bootstrap_iterations": 1000,
        "pvalue_correction": "bonferroni",
        "sensitivity_factors": [1.5, 2.0, 2.5]
    },
    "data": {
        "is_synthetic": False,
        "raw_dir": "data/raw",
        "processed_dir": "data/processed",
        "results_dir": "results",
        "state_dir": "state",
        "logs_dir": "logs"
    },
    "logging": {
        "level": "INFO",
        "format": "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
        "file": "logs/pipeline.log",
        "rotation_max_bytes": 10485760,
        "rotation_backup_count": 3
    }
}

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Configuration manager class.
    
    Loads configuration from a YAML file and provides access to all settings.
    Falls back to defaults if a key is missing.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the config.yaml file. If None, searches in 
                         standard locations.
        """
        self.config_path = config_path or self._find_config()
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _find_config(self) -> str:
        """
        Find the config.yaml file in standard locations.
        
        Priority:
        1. Current working directory
        2. Project root (parent of 'code' or 'src' directory)
        3. Default to 'config.yaml' in current directory
        
        Returns:
            Path to the config file.
        """
        # Check current directory
        if os.path.exists("config.yaml"):
            return "config.yaml"
        
        # Check project root (assuming we are in code/ or src/)
        current = Path.cwd()
        for parent in current.parents:
            if (parent / "config.yaml").exists():
                return str(parent / "config.yaml")
        
        # Default fallback
        return "config.yaml"
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    self._config = self._deep_merge(DEFAULT_CONFIG, loaded_config)
            else:
                # Use defaults if file doesn't exist
                self._config = DEFAULT_CONFIG
                # Create the file with defaults
                self.save(self.config_path)
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse config file {self.config_path}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config file {self.config_path}: {e}")
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary to merge on top
        
        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-separated key.
        
        Args:
            key: Dot-separated key path (e.g., 'simulation.distance_threshold_nm')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            path: Path to save to. If None, uses the original config path.
        """
        save_path = path or self.config_path
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise ConfigError(f"Failed to save config file {save_path}: {e}")
    
    @property
    def simulation(self) -> Dict[str, Any]:
        """Get simulation configuration."""
        return self._config.get("simulation", {})
    
    @property
    def distance_threshold(self) -> float:
        """Get the distance threshold in nanometers."""
        return self.simulation.get("distance_threshold_nm", 2.0)
    
    @property
    def seed(self) -> int:
        """Get the random seed."""
        return self._config.get("project", {}).get("seed", 42)
    
    @property
    def materials(self) -> Dict[str, Any]:
        """Get material constants."""
        return self._config.get("materials", {})
    
    @property
    def analysis(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self._config.get("analysis", {})
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get data paths and settings."""
        return self._config.get("data", {})
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self._config.get("logging", {})
    
    def get_material_constant(self, material: str, constant: str, default: Any = None) -> Any:
        """
        Get a specific material constant.
        
        Args:
            material: Material name (e.g., 'graphene')
            constant: Constant name (e.g., 'lattice_constant_nm')
            default: Default value if not found
        
        Returns:
            Material constant value
        """
        materials = self.materials.get(material, {})
        return materials.get(constant, default)

# Global config instance (lazy initialization)
_global_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Global Config instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config
