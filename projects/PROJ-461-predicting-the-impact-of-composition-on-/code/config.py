"""
Configuration management for the Metallic Glass Density Prediction project.

This module provides a centralized configuration system that loads settings
from environment variables (.env) or a YAML config file.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Config:
    """
    Project configuration container.
    
    Attributes:
        seed: Random seed for reproducibility.
        data_dir: Path to the data directory.
        model_dir: Path to the model directory.
        report_dir: Path to the reports directory.
    """
    seed: int = 42
    data_dir: Path = field(default_factory=lambda: Path("data"))
    model_dir: Path = field(default_factory=lambda: Path("models"))
    report_dir: Path = field(default_factory=lambda: Path("reports"))
    
    def __post_init__(self):
        """Ensure paths are Path objects and log configuration."""
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.model_dir, str):
            self.model_dir = Path(self.model_dir)
        if isinstance(self.report_dir, str):
            self.report_dir = Path(self.report_dir)
        
        logger.info(f"Configuration initialized: seed={self.seed}")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Model directory: {self.model_dir}")
        logger.info(f"Report directory: {self.report_dir}")


def load_config(env_path: Optional[str] = None, yaml_path: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables or YAML file.
    
    Priority:
    1. Environment variables (from .env file if specified)
    2. YAML config file (if specified)
    3. Default values
    
    Args:
        env_path: Path to .env file. Defaults to '.env' in project root.
        yaml_path: Path to config.yaml. Defaults to 'config.yaml' in project root.
        
    Returns:
        Config: Initialized configuration object.
    """
    # Default paths
    if env_path is None:
        env_path = Path.cwd() / ".env"
    else:
        env_path = Path(env_path)
        
    if yaml_path is None:
        yaml_path = Path.cwd() / "config.yaml"
    else:
        yaml_path = Path(yaml_path)
    
    # Load environment variables from .env file if it exists
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        _load_dotenv(env_path)
    else:
        logger.debug(f"No .env file found at {env_path}")
    
    # Initialize config with defaults
    config_dict = {
        "seed": int(os.getenv("SEED", 42)),
        "data_dir": os.getenv("DATA_DIR", "data"),
        "model_dir": os.getenv("MODEL_DIR", "models"),
        "report_dir": os.getenv("REPORT_DIR", "reports"),
    }
    
    # Override with YAML config if it exists
    if yaml_path.exists():
        logger.info(f"Loading configuration from {yaml_path}")
        try:
            with open(yaml_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                
            if yaml_config:
                # Update config_dict with YAML values
                for key in config_dict.keys():
                    if key in yaml_config:
                        config_dict[key] = yaml_config[key]
                        logger.debug(f"Overriding {key} from YAML: {config_dict[key]}")
        except yaml.YAMLError as e:
            logger.warning(f"Error parsing YAML config: {e}. Using environment/config defaults.")
    else:
        logger.debug(f"No YAML config file found at {yaml_path}")
    
    # Create and return Config object
    return Config(
        seed=config_dict["seed"],
        data_dir=Path(config_dict["data_dir"]),
        model_dir=Path(config_dict["model_dir"]),
        report_dir=Path(config_dict["report_dir"]),
    )


def _load_dotenv(env_path: Path) -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file.
    """
    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Parse key=value pairs
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Set environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value
                        logger.debug(f"Set environment variable: {key}")
    except Exception as e:
        logger.warning(f"Error loading .env file: {e}")


# Convenience function to get default config
def get_default_config() -> Config:
    """
    Get configuration with default values.
    
    Returns:
        Config: Configuration object with default values.
    """
    return Config()
