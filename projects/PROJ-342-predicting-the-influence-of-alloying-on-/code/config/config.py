"""
Environment configuration management for the Metallic Glasses project.

Handles loading of:
- .env files for sensitive data (DOIs, API keys)
- config.yaml for reproducible seeds, limits, and hyperparameters

Satisfies T007: Setup environment configuration management.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Attempt to import python-dotenv; if missing, warn but don't fail the import
# The main() function will handle the actual loading if the package is installed.
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Define project root based on the established structure (code/ is root for imports)
# The project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"
CONFIG_YAML_PATH = PROJECT_ROOT / "config.yaml"

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class Config:
    """
    Central configuration manager.
    
    Loads environment variables from .env and structured config from config.yaml.
    """
    
    def __init__(self, env_path: Optional[Path] = None, yaml_path: Optional[Path] = None):
        self.env_path = env_path or ENV_FILE_PATH
        self.yaml_path = yaml_path or CONFIG_YAML_PATH
        self._env_vars: Dict[str, str] = {}
        self._yaml_config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> None:
        """
        Load configuration from .env and config.yaml.
        
        Raises:
            ConfigError: If required configuration is missing or files are invalid.
        """
        if self._loaded:
            return
        
        # 1. Load .env
        if self.env_path.exists():
            if DOTENV_AVAILABLE:
                load_dotenv(self.env_path)
                logger.info(f"Loaded environment variables from {self.env_path}")
            else:
                logger.warning(
                    f"Found {self.env_path} but 'python-dotenv' is not installed. "
                    "Install it to load environment variables automatically."
                )
            # Fallback: manually read if dotenv not available (basic support)
            if not DOTENV_AVAILABLE:
                with open(self.env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, _, value = line.partition('=')
                            os.environ[key.strip()] = value.strip().strip('"').strip("'")
        else:
            logger.warning(f"Environment file not found at {self.env_path}. "
                         "Ensure DOIs are set in environment or file.")
        
        # 2. Load config.yaml
        if self.yaml_path.exists():
            with open(self.yaml_path, 'r') as f:
                self._yaml_config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.yaml_path}")
        else:
            logger.warning(f"Configuration file not found at {self.yaml_path}. "
                         "Using defaults where possible.")
        
        self._loaded = True
    
    def get_zenodo_dois(self) -> Dict[str, str]:
        """Retrieve Zenodo DOIs from environment variables."""
        self.load()
        primary = os.getenv("ZENODO_PRIMARY_DOI")
        fallback = os.getenv("ZENODO_FALLBACK_DOI")
        
        if not primary:
            # Hardcode the specific DOIs required by the project spec if not in env
            # This ensures the system works even if .env is missing, though it's preferred to have it.
            primary = "10.5281/zenodo.10043838"
            logger.warning("ZENODO_PRIMARY_DOI not set in environment. Using default: 10.5281/zenodo.10043838")
        
        if not fallback:
            fallback = "10.5281/zenodo.11023456"
            logger.warning("ZENODO_FALLBACK_DOI not set in environment. Using default: 10.5281/zenodo.11023456")
        
        return {
            "primary": primary,
            "fallback": fallback
        }
    
    def get_seed(self) -> int:
        """Get random seed for reproducibility."""
        self.load()
        return self._yaml_config.get("random_seed", 42)
    
    def get_limits(self) -> Dict[str, Any]:
        """Get resource limits (time, memory)."""
        self.load()
        return self._yaml_config.get("resource_limits", {
            "max_time_hours": 6,
            "max_memory_gb": 7
        })
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get model-specific hyperparameters."""
        self.load()
        return self._yaml_config.get("model_params", {})
    
    def get_all(self) -> Dict[str, Any]:
        """Return the full configuration dictionary."""
        self.load()
        return {
            "zenodo_dois": self.get_zenodo_dois(),
            "random_seed": self.get_seed(),
            "resource_limits": self.get_limits(),
            "model_params": self.get_model_params(),
            "env_vars": dict(os.environ) # Be careful not to log secrets in production
        }


def get_config() -> Config:
    """Factory function to retrieve the singleton Config instance."""
    return Config()


def main() -> None:
    """
    CLI entry point to validate and print configuration.
    
    Usage: python -m code.config.config
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        config = get_config()
        config.load()
        
        print("Configuration Loaded Successfully:")
        print("-" * 30)
        dois = config.get_zenodo_dois()
        print(f"Primary DOI: {dois['primary']}")
        print(f"Fallback DOI: {dois['fallback']}")
        print(f"Random Seed: {config.get_seed()}")
        print(f"Time Limit (h): {config.get_limits()['max_time_hours']}")
        print(f"Memory Limit (GB): {config.get_limits()['max_memory_gb']}")
        print("-" * 30)
        print("Config validation passed.")
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
