"""
Descriptor Registry Module

This module provides functionality to load and manage the configuration
for molecular descriptors defined in config/descriptors.yaml.

It ensures that the pipeline calculates exactly the descriptors specified
in the configuration file, with strict adherence to the defined methods
and parameters.
"""

import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup logging
logger = logging.getLogger(__name__)

# Default path relative to project root
DEFAULT_CONFIG_PATH = Path("config/descriptors.yaml")

class DescriptorRegistryError(Exception):
    """Custom exception for descriptor registry errors."""
    pass

class DescriptorConfig:
    """
    Container for a single descriptor configuration entry.
    
    Attributes:
        name (str): The unique name of the descriptor.
        method (str): The calculation method (e.g., 'rdkit_calculation', 'psi4_calculation').
        parameters (dict): Parameters specific to the calculation method.
        description (str): Human-readable description of the descriptor.
    """
    def __init__(self, config_dict: Dict[str, Any]):
        self.name = config_dict.get('name')
        self.method = config_dict.get('method')
        self.parameters = config_dict.get('parameters', {})
        self.description = config_dict.get('description', '')
        
        if not self.name or not self.method:
            raise DescriptorRegistryError(
                f"Descriptor configuration missing required 'name' or 'method': {config_dict}"
            )
    
    def __repr__(self) -> str:
        return f"DescriptorConfig(name={self.name}, method={self.method})"

class DescriptorRegistry:
    """
    Registry for managing descriptor configurations.
    
    This class loads the configuration from the YAML file and provides
    access to the descriptor definitions. It acts as a central source
    of truth for what descriptors need to be calculated and how.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the Descriptor Registry.
        
        Args:
            config_path: Path to the YAML configuration file. Defaults to DEFAULT_CONFIG_PATH.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._descriptors: Dict[str, DescriptorConfig] = {}
        self._raw_config: Dict[str, Any] = {}
        
        if not self.config_path.exists():
            raise DescriptorRegistryError(
                f"Descriptor configuration file not found at: {self.config_path}"
            )
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f)
            
            if not isinstance(self._raw_config, dict):
                raise DescriptorRegistryError("Invalid YAML structure: expected a dictionary at root level")
            
            descriptor_list = self._raw_config.get('descriptors', [])
            if not descriptor_list:
                raise DescriptorRegistryError("No descriptors found in configuration file")
            
            for entry in descriptor_list:
                config = DescriptorConfig(entry)
                self._descriptors[config.name] = config
                logger.debug(f"Loaded descriptor config: {config.name}")
            
            logger.info(f"Loaded {len(self._descriptors)} descriptor configurations from {self.config_path}")
            
        except yaml.YAMLError as e:
            raise DescriptorRegistryError(f"Failed to parse YAML configuration: {e}")
        except Exception as e:
            raise DescriptorRegistryError(f"Failed to load descriptor configuration: {e}")
    
    def get_descriptor(self, name: str) -> DescriptorConfig:
        """
        Retrieve a specific descriptor configuration by name.
        
        Args:
            name: The name of the descriptor to retrieve.
        
        Returns:
            DescriptorConfig: The configuration object for the requested descriptor.
        
        Raises:
            DescriptorRegistryError: If the descriptor is not found.
        """
        if name not in self._descriptors:
            raise DescriptorRegistryError(f"Descriptor '{name}' not found in registry")
        return self._descriptors[name]
    
    def get_all_descriptors(self) -> List[DescriptorConfig]:
        """
        Retrieve all registered descriptor configurations.
        
        Returns:
            List[DescriptorConfig]: A list of all descriptor configurations.
        """
        return list(self._descriptors.values())
    
    def get_descriptor_names(self) -> List[str]:
        """
        Retrieve the names of all registered descriptors.
        
        Returns:
            List[str]: A list of descriptor names.
        """
        return list(self._descriptors.keys())
    
    def validate_descriptors(self, required_names: List[str]) -> List[str]:
        """
        Check if all required descriptors are present in the registry.
        
        Args:
            required_names: List of required descriptor names.
        
        Returns:
            List[str]: List of missing descriptor names.
        """
        missing = []
        for name in required_names:
            if name not in self._descriptors:
                missing.append(name)
        return missing

def load_descriptor_registry(config_path: Optional[Path] = None) -> DescriptorRegistry:
    """
    Convenience function to load the descriptor registry.
    
    Args:
        config_path: Optional path to the configuration file.
    
    Returns:
        DescriptorRegistry: The loaded registry instance.
    """
    return DescriptorRegistry(config_path)

def main():
    """
    Main entry point for testing the descriptor registry.
    Loads the configuration and prints summary information.
    """
    try:
        registry = load_descriptor_registry()
        
        print(f"Descriptor Registry loaded successfully from: {registry.config_path}")
        print(f"Total descriptors registered: {len(registry.get_all_descriptors())}")
        print("\nRegistered Descriptors:")
        for desc in registry.get_all_descriptors():
            print(f"  - {desc.name}: {desc.description}")
            print(f"    Method: {desc.method}")
            print(f"    Parameters: {desc.parameters}")
            print()
        
        # Validate that all required descriptors from the task are present
        required = ['kinetic_diameter', 'lj_epsilon', 'quadrupole_moment', 'polarizability', 'vdw_volume']
        missing = registry.validate_descriptors(required)
        
        if missing:
            print(f"ERROR: Missing required descriptors: {missing}")
            sys.exit(1)
        else:
            print("SUCCESS: All required descriptors are present in the registry.")
            
    except DescriptorRegistryError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()