"""
Environment configuration management for random seeds and file paths.

This module provides centralized configuration handling for the corrosion
prediction pipeline, ensuring reproducibility through random seed management
and consistent file path resolution.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml

from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProjectConfig:
    """
    Centralized project configuration.
    
    Attributes:
        project_root: Root directory of the project
        data_dir: Directory for all data files
        data_raw_dir: Directory for raw data
        data_processed_dir: Directory for processed data
        data_logs_dir: Directory for log files
        state_dir: Directory for state files
        config_dir: Directory for configuration files
        code_dir: Directory for code files
        models_dir: Directory for model artifacts
        utils_dir: Directory for utility modules
        tests_dir: Directory for test files
        contracts_dir: Directory for schema contracts
        random_seed: Random seed for reproducibility
        environment: Current environment (development, testing, production)
        verbose: Verbosity level for logging
    """
    project_root: Path
    data_dir: Path = field(init=False)
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    data_logs_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    code_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    utils_dir: Path = field(init=False)
    tests_dir: Path = field(init=False)
    contracts_dir: Path = field(init=False)
    random_seed: int = 42
    environment: str = "development"
    verbose: bool = True

    def __post_init__(self):
        """Initialize derived paths based on project_root."""
        self.data_dir = self.project_root / "data"
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.state_dir = self.project_root / "state"
        self.config_dir = self.project_root / "config"
        self.code_dir = self.project_root / "code"
        self.models_dir = self.code_dir / "models"
        self.utils_dir = self.code_dir / "utils"
        self.tests_dir = self.code_dir / "tests"
        self.contracts_dir = self.project_root / "contracts"

        # Ensure all directories exist
        for dir_path in [
            self.data_dir, self.data_raw_dir, self.data_processed_dir,
            self.data_logs_dir, self.state_dir, self.config_dir,
            self.code_dir, self.models_dir, self.utils_dir,
            self.tests_dir, self.contracts_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "data_raw_dir": str(self.data_raw_dir),
            "data_processed_dir": str(self.data_processed_dir),
            "data_logs_dir": str(self.data_logs_dir),
            "state_dir": str(self.state_dir),
            "config_dir": str(self.config_dir),
            "random_seed": self.random_seed,
            "environment": self.environment,
            "verbose": self.verbose
        }

    def save_to_yaml(self, path: Optional[Path] = None) -> None:
        """Save configuration to YAML file."""
        if path is None:
            path = self.config_dir / "project_config.yaml"
        
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {path}")


class ConfigManager:
    """
    Manages project configuration and random seed initialization.
    
    This class provides methods to load, create, and manage project configuration,
    as well as to set random seeds for reproducibility across numpy, random, and
    torch (if available).
    """
    
    _instance: Optional['ConfigManager'] = None
    _config: Optional[ProjectConfig] = None

    def __new__(cls):
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration manager."""
        if self._config is not None:
            return
        
        # Try to load from existing config file
        config_path = Path("config") / "project_config.yaml"
        if config_path.exists():
            self._config = self._load_from_yaml(config_path)
            logger.info(f"Loaded configuration from {config_path}")
        else:
            # Create default configuration
            project_root = Path(__file__).resolve().parent.parent.parent
            self._config = ProjectConfig(project_root=project_root)
            logger.info("Created default configuration")

    @classmethod
    def get_config(cls) -> ProjectConfig:
        """Get the current configuration."""
        instance = cls()
        return instance._config

    @classmethod
    def set_random_seed(cls, seed: Optional[int] = None) -> None:
        """
        Set random seeds for reproducibility.
        
        Args:
            seed: Random seed value. If None, uses the seed from configuration.
        """
        if seed is None:
            seed = cls.get_config().random_seed
        
        # Set seed for Python's random module
        random.seed(seed)
        logger.info(f"Set random seed to {seed}")

        # Set seed for numpy if available
        try:
            import numpy as np
            np.random.seed(seed)
            logger.debug("Set numpy random seed")
        except ImportError:
            logger.debug("numpy not available, skipping numpy seed")

        # Set seed for torch if available
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)
            logger.debug("Set torch random seed")
        except ImportError:
            logger.debug("torch not available, skipping torch seed")

    @classmethod
    def _load_from_yaml(cls, path: Path) -> ProjectConfig:
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        project_root = Path(data.get("project_root", Path(__file__).resolve().parent.parent.parent))
        
        return ProjectConfig(
            project_root=project_root,
            random_seed=data.get("random_seed", 42),
            environment=data.get("environment", "development"),
            verbose=data.get("verbose", True)
        )

    @classmethod
    def save_config(cls, path: Optional[Path] = None) -> None:
        """Save current configuration to YAML file."""
        cls.get_config().save_to_yaml(path)

    @classmethod
    def update_config(cls, **kwargs) -> None:
        """
        Update configuration with new values.
        
        Args:
            **kwargs: Key-value pairs to update in configuration.
        """
        config = cls.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                logger.debug(f"Updated config.{key} to {value}")
            else:
                logger.warning(f"Unknown configuration key: {key}")

    @classmethod
    def get_path(cls, *paths) -> Path:
        """
        Get an absolute path relative to project root.
        
        Args:
            *paths: Path components to join with project root.
        
        Returns:
            Absolute Path object.
        """
        config = cls.get_config()
        return config.project_root / Path(*paths)

    @classmethod
    def get_data_path(cls, *paths) -> Path:
        """Get a path relative to the data directory."""
        config = cls.get_config()
        return config.data_dir / Path(*paths)

    @classmethod
    def get_processed_data_path(cls, *paths) -> Path:
        """Get a path relative to the processed data directory."""
        config = cls.get_config()
        return config.data_processed_dir / Path(*paths)

    @classmethod
    def get_log_path(cls, *paths) -> Path:
        """Get a path relative to the logs directory."""
        config = cls.get_config()
        return config.data_logs_dir / Path(*paths)


# Convenience functions for common operations
def get_config() -> ProjectConfig:
    """Get the current project configuration."""
    return ConfigManager.get_config()

def set_random_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    ConfigManager.set_random_seed(seed)

def get_path(*paths) -> Path:
    """Get an absolute path relative to project root."""
    return ConfigManager.get_path(*paths)

def get_data_path(*paths) -> Path:
    """Get a path relative to the data directory."""
    return ConfigManager.get_data_path(*paths)

def get_processed_data_path(*paths) -> Path:
    """Get a path relative to the processed data directory."""
    return ConfigManager.get_processed_data_path(*paths)

def get_log_path(*paths) -> Path:
    """Get a path relative to the logs directory."""
    return ConfigManager.get_log_path(*paths)

def save_config(path: Optional[Path] = None) -> None:
    """Save current configuration to YAML file."""
    ConfigManager.save_config(path)

def update_config(**kwargs) -> None:
    """Update configuration with new values."""
    ConfigManager.update_config(**kwargs)
