"""
Environment configuration management for API keys and random seeds.

This module provides a centralized configuration manager that:
1. Loads API keys from environment variables (with optional .env file support)
2. Manages random seed pinning for reproducibility
3. Provides a global configuration singleton accessible across the project
"""

import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Attempt to import dotenv for .env file support
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    logging.warning("python-dotenv not installed. .env file support disabled.")

from utils import pin_seed, setup_logging


class Config:
    """
    Global configuration manager for the project.

    Handles:
    - API key retrieval (Materials Project, etc.)
    - Random seed management
    - Path configuration
    """

    _instance: Optional['Config'] = None
    _initialized: bool = False

    def __init__(self):
        if self._initialized:
            return
        
        self._logger = setup_logging("config", level=logging.INFO)
        self._api_keys: Dict[str, str] = {}
        self._random_seed: Optional[int] = None
        self._paths: Dict[str, Path] = {}
        
        self._load_environment()
        self._initialize_paths()
        self._initialized = True

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get the singleton instance of Config."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)."""
        if cls._instance:
            cls._instance._initialized = False
            cls._instance = None

    def _load_environment(self):
        """Load environment variables and .env file if available."""
        # Try to load .env file from project root
        env_path = Path(__file__).parent.parent / '.env'
        if HAS_DOTENV and env_path.exists():
            load_dotenv(env_path)
            self._logger.info(f"Loaded .env file from {env_path}")

        # Load Materials Project API key
        mp_key = os.getenv('MATERIALS_PROJECT_API_KEY')
        if mp_key:
            self._api_keys['materials_project'] = mp_key
            self._logger.info("Materials Project API key loaded from environment")
        else:
            self._logger.warning("MATERIALS_PROJECT_API_KEY not found in environment")

        # Load random seed
        seed_str = os.getenv('RANDOM_SEED')
        if seed_str:
            try:
                self._random_seed = int(seed_str)
                self._logger.info(f"Random seed set from environment: {self._random_seed}")
            except ValueError:
                self._logger.warning(f"Invalid RANDOM_SEED value: {seed_str}, using default")
                self._random_seed = 42
        else:
            self._random_seed = 42
            self._logger.info("Using default random seed: 42")

    def _initialize_paths(self):
        """Initialize project path configuration."""
        base_path = Path(__file__).parent.parent
        
        self._paths = {
            'base': base_path,
            'data_raw': base_path / 'data' / 'raw',
            'data_processed': base_path / 'data' / 'processed',
            'models': base_path / 'models',
            'results': base_path / 'results',
            'code': base_path / 'code',
            'cif_files': base_path / 'data' / 'raw' / 'cif',
            'networks': base_path / 'data' / 'processed' / 'networks'
        }

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service.

        Args:
            service: Service name (e.g., 'materials_project')

        Returns:
            API key string or None if not found
        """
        return self._api_keys.get(service)

    def get_random_seed(self) -> int:
        """
        Get the current random seed.

        Returns:
            Integer random seed
        """
        return self._random_seed

    def set_random_seed(self, seed: int):
        """
        Set a new random seed and update global state.

        Args:
            seed: New random seed value
        """
        self._random_seed = seed
        pin_seed(seed)
        self._logger.info(f"Random seed updated to: {seed}")

    def get_path(self, key: str) -> Optional[Path]:
        """
        Get a configured path by key.

        Args:
            key: Path key (e.g., 'data_raw', 'models')

        Returns:
            Path object or None if key not found
        """
        return self._paths.get(key)

    def ensure_directories(self):
        """Ensure all configured directories exist."""
        for path in self._paths.values():
            if path:
                path.mkdir(parents=True, exist_ok=True)
                self._logger.debug(f"Ensured directory exists: {path}")

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as a dictionary (excluding sensitive data)."""
        return {
            'random_seed': self._random_seed,
            'paths': {k: str(v) for k, v in self._paths.items() if v},
            'api_keys_configured': list(self._api_keys.keys()),
            'dotenv_available': HAS_DOTENV
        }


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config singleton instance
    """
    return Config.get_instance()


def reset_config():
    """Reset the global configuration (useful for testing)."""
    Config.reset()


def initialize_environment(seed: Optional[int] = None, env_file: Optional[Path] = None):
    """
    Initialize the environment with optional custom seed and .env file.

    Args:
        seed: Optional custom random seed
        env_file: Optional path to .env file
    """
    config = get_config()
    
    if env_file and HAS_DOTENV:
        load_dotenv(env_file)
    
    if seed is not None:
        config.set_random_seed(seed)
    
    config.ensure_directories()
    
    return config


def main():
    """Main entry point for configuration testing."""
    print("=== Project Configuration ===")
    
    config = get_config()
    
    print(f"Random Seed: {config.get_random_seed()}")
    print(f"Base Path: {config.get_path('base')}")
    print(f"Data Raw: {config.get_path('data_raw')}")
    print(f"Data Processed: {config.get_path('data_processed')}")
    print(f"Models: {config.get_path('models')}")
    print(f"Results: {config.get_path('results')}")
    
    mp_key = config.get_api_key('materials_project')
    if mp_key:
        print(f"Materials Project API Key: {'*' * 8}{mp_key[-4:]}")
    else:
        print("Materials Project API Key: NOT CONFIGURED")
    
    print("\nConfiguration initialization complete.")
    print("To set API keys, add to .env file or environment variables:")
    print("  MATERIALS_PROJECT_API_KEY=your_key_here")
    print("  RANDOM_SEED=42")


if __name__ == '__main__':
    main()
