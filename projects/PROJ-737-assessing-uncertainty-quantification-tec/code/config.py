"""
Environment configuration management for the UQ pipeline.

Handles loading of .env files for API keys and config.yaml for hyperparameters.
Provides a central Config object to access these settings throughout the pipeline.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from utils.logger import get_logger

logger = get_logger(__name__)

# Default paths
DEFAULT_ENV_PATH = ".env"
DEFAULT_CONFIG_PATH = "config.yaml"

class Config:
    """Central configuration manager for the project."""
    
    def __init__(self, env_path: Optional[str] = None, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_path: Path to .env file. Defaults to .env in project root.
            config_path: Path to config.yaml. Defaults to config.yaml in project root.
        """
        self.project_root = Path(__file__).parent.parent
        self.env_path = Path(env_path) if env_path else self.project_root / DEFAULT_ENV_PATH
        self.config_path = Path(config_path) if config_path else self.project_root / DEFAULT_CONFIG_PATH
        
        self._env_vars: Dict[str, str] = {}
        self._hyperparams: Dict[str, Any] = {}
        
        self._load_env()
        self._load_config()
        
    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if self.env_path.exists():
            load_dotenv(self.env_path)
            logger.info(f"Loaded environment variables from {self.env_path}")
        else:
            logger.warning(f"Environment file not found at {self.env_path}. "
                         "Using system environment variables only.")
        
        # Store a copy of relevant env vars for access
        self._env_vars = dict(os.environ)

    def _load_config(self) -> None:
        """Load hyperparameters from config.yaml file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self._hyperparams = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML config file: {e}")
                raise
        else:
            logger.warning(f"Config file not found at {self.config_path}. "
                         "Using default hyperparameters.")
            self._hyperparams = self._get_default_hyperparams()

    def _get_default_hyperparams(self) -> Dict[str, Any]:
        """Return default hyperparameters if config file is missing."""
        return {
            "data": {
                "max_samples": 1000,
                "test_size": 0.2,
                "validation_size": 0.1,
                "random_seed": 42,
                "memory_limit_gb": 1.8
            },
            "models": {
                "gpr": {
                    "kernel": "RBF",
                    "alpha": 1e-10,
                    "n_restarts_optimizer": 5
                },
                "mc_dropout": {
                    "dropout_rate": 0.1,
                    "num_mc_samples": 100,
                    "max_epochs": 100,
                    "convergence_threshold": 1e-4,
                    "convergence_window": 50
                },
                "deep_ensemble": {
                    "num_models": 3,
                    "max_epochs": 100,
                    "early_stopping_patience": 10
                },
                "conformal": {
                    "coverage_levels": [0.80, 0.85, 0.90, 0.95, 0.99],
                    "calibration_size": 0.1
                }
            },
            "metrics": {
                "nominal_coverage": 0.95,
                "sharpness_weight": 1.0
            },
            "stats": {
                "significance_level": 0.05,
                "sensitivity_coverage_range": {
                    "start": 0.80,
                    "end": 0.99,
                    "step": 0.01
                }
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a hyperparameter value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., "data.max_samples", "models.gpr.kernel")
            default: Default value if key not found
            
        Returns:
            The value for the key, or default if not found
        """
        keys = key.split('.')
        value = self._hyperparams
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            The environment variable value or default
        """
        return self._env_vars.get(key, default)

    @property
    def data_config(self) -> Dict[str, Any]:
        """Get data configuration section."""
        return self._hyperparams.get("data", {})

    @property
    def models_config(self) -> Dict[str, Any]:
        """Get models configuration section."""
        return self._hyperparams.get("models", {})

    @property
    def stats_config(self) -> Dict[str, Any]:
        """Get stats configuration section."""
        return self._hyperparams.get("stats", {})

    def __repr__(self) -> str:
        return f"Config(env_path={self.env_path}, config_path={self.config_path})"

# Global config instance (lazy loaded)
_config_instance: Optional[Config] = None

def get_config(env_path: Optional[str] = None, config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.
    
    Args:
        env_path: Optional path to override .env location
        config_path: Optional path to override config.yaml location
        
    Returns:
        The global Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_path, config_path)
    return _config_instance

def reload_config() -> Config:
    """Force reload of configuration."""
    global _config_instance
    _config_instance = None
    return get_config()

if __name__ == "__main__":
    # Simple test of config loading
    cfg = get_config()
    print(f"Loaded config from: {cfg.config_path}")
    print(f"Data max_samples: {cfg.get('data.max_samples')}")
    print(f"Random seed: {cfg.get('data.random_seed')}")
    print(f"GPR kernel: {cfg.get('models.gpr.kernel')}")
    print(f"MC dropout rate: {cfg.get('models.mc_dropout.dropout_rate')}")
