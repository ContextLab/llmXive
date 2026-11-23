"""
Environment configuration management for random seeds and file paths.

This module provides a centralized configuration system for the corrosion prediction
pipeline, handling random seed management, path resolution, and configuration
persistence.
"""
import os
import random
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from utils.logging import get_logger
from utils.exceptions import CorrosionPipelineError

logger = get_logger(__name__)


@dataclass
class ProjectConfig:
    """Dataclass holding all project configuration parameters."""
    
    # Random seed configuration
    random_seed: int = 42
    
    # Path configurations
    project_root: str = ""
    data_root: str = "data"
    code_root: str = "code"
    config_root: str = "config"
    state_root: str = "state"
    contracts_root: str = "contracts"
    logs_root: str = "data/logs"
    
    # Subdirectory paths (relative to data_root)
    data_raw: str = "data/raw"
    data_processed: str = "data/processed"
    data_figures: str = "data/figures"
    data_interpretability: str = "data/processed/interpretability"
    logs_diagnostics: str = "data/logs/diagnostics"
    
    # Specific file paths (relative to their root)
    pipeline_log: str = "data/logs/pipeline.log"
    count_report: str = "data/logs/diagnostics/count_report.txt"
    split_validation: str = "data/logs/split_validation.json"
    model_results: str = "data/processed/model_results.json"
    processed_dataset: str = "data/processed/corrosion_dataset.parquet"
    split_indices: str = "data/processed/split_indices.json"
    verified_datasets_config: str = "config/verified_datasets.yaml"
    astm_tolerance_config: str = "config/astm_g59_tolerance.yaml"
    
    # Feature flags
    use_streaming: bool = True
    strict_validation: bool = True
    log_all_exclusions: bool = True
    
    # Model training parameters
    random_forest_n_estimators: int = 100
    gradient_boosting_n_estimators: int = 100
    groupkfold_k: int = 5
    permutation_test_permutations: int = 1000
    
    # Data thresholds
    minimum_records: int = 500
    minimum_alloy_designations: int = 10
    
    def __post_init__(self):
        """Initialize project_root if not set."""
        if not self.project_root:
            # Try to detect from current working directory
            self.project_root = str(Path.cwd())
            logger.info(f"Auto-detected project root: {self.project_root}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Create config from dictionary."""
        return cls(**data)


class ConfigManager:
    """Manages configuration loading, saving, and retrieval."""
    
    _instance = None
    _config: Optional[ProjectConfig] = None
    
    def __init__(self):
        if self._instance is not None:
            raise RuntimeError("ConfigManager is singleton. Use get_config() instead.")
        
        self._config = None
        self._config_path: Optional[Path] = None
        
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = ConfigManager()
        return cls._instance
    
    def initialize(self, config_path: Optional[Path] = None) -> ProjectConfig:
        """
        Initialize configuration from file or defaults.
        
        Args:
            config_path: Path to YAML config file. If None, uses defaults.
        
        Returns:
            Loaded or default ProjectConfig instance.
        """
        if config_path is None:
            # Default path
            config_path = Path("config/pipeline_config.yaml")
        else:
            config_path = Path(config_path)
        
        self._config_path = config_path
        
        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
            try:
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)
                self._config = ProjectConfig.from_dict(config_data)
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
                self._config = ProjectConfig()
        else:
            logger.info(f"Config file {config_path} not found. Using defaults.")
            self._config = ProjectConfig()
        
        return self._config
    
    def get_config(self) -> ProjectConfig:
        """Get current configuration."""
        if self._config is None:
            self.initialize()
        return self._config
    
    def save_config(self, config: Optional[ProjectConfig] = None, 
                   path: Optional[Path] = None) -> Path:
        """
        Save configuration to YAML file.
        
        Args:
            config: Config to save. If None, uses current config.
            path: Output path. If None, uses default path.
        
        Returns:
            Path to saved config file.
        """
        if config is None:
            config = self.get_config()
        
        if path is None:
            if self._config_path is None:
                path = Path("config/pipeline_config.yaml")
            else:
                path = self._config_path
        else:
            path = Path(path)
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {path}")
        return path


# Global config manager instance
_config_manager = ConfigManager.get_instance()


def get_config() -> ProjectConfig:
    """Get the global project configuration."""
    return _config_manager.get_config()


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set random seed for reproducibility across all libraries.
    
    Args:
        seed: Seed value. If None, uses config value.
        
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = get_config().random_seed
    
    # Set for Python
    random.seed(seed)
    
    # Set for numpy (if available)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.debug("numpy not available, skipping numpy seed")
    
    # Set for PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        logger.debug("torch not available, skipping torch seed")
    
    logger.info(f"Random seed set to {seed}")
    return seed


def get_path(key: str) -> Path:
    """
    Get a path from configuration by key.
    
    Args:
        key: Configuration key (e.g., 'data_root', 'pipeline_log')
        
    Returns:
        Absolute Path object.
        
    Raises:
        CorrosionPipelineError: If key not found in config.
    """
    config = get_config()
    config_dict = config.to_dict()
    
    if key not in config_dict:
        raise CorrosionPipelineError(f"Configuration key '{key}' not found")
    
    path_str = config_dict[key]
    
    # If path is absolute, use as-is
    if path_str.startswith("/"):
        return Path(path_str)
    
    # Otherwise, make relative to project_root
    project_root = Path(config.project_root)
    return project_root / path_str


def get_data_path(subpath: Optional[str] = None) -> Path:
    """
    Get the data root or a subpath within data.
    
    Args:
        subpath: Optional subpath relative to data root.
        
    Returns:
        Absolute Path object.
    """
    data_root = get_path("data_root")
    if subpath:
        return data_root / subpath
    return data_root


def get_processed_data_path(filename: str) -> Path:
    """Get path to a processed data file."""
    return get_path("data_processed") / filename


def get_log_path(filename: str) -> Path:
    """Get path to a log file."""
    return get_path("logs_root") / filename


def get_config_path(filename: str) -> Path:
    """Get path to a config file."""
    return get_path("config_root") / filename


def get_state_path(filename: str) -> Path:
    """Get path to a state file."""
    return get_path("state_root") / filename


def get_contracts_path(filename: str) -> Path:
    """Get path to a contract file."""
    return get_path("contracts_root") / filename


# Specific path getters for common files
def get_processed_dataset_path() -> Path:
    """Get path to the processed corrosion dataset."""
    return get_path("processed_dataset")


def get_model_results_path() -> Path:
    """Get path to model results JSON."""
    return get_path("model_results")


def get_pipeline_log_path() -> Path:
    """Get path to the pipeline log."""
    return get_path("pipeline_log")


def get_split_indices_path() -> Path:
    """Get path to split indices JSON."""
    return get_path("split_indices")


def get_split_validation_path() -> Path:
    """Get path to split validation JSON."""
    return get_path("split_validation")


def get_diagnostics_path() -> Path:
    """Get path to diagnostics directory."""
    return get_path("logs_diagnostics")


def get_count_report_path() -> Path:
    """Get path to count report file."""
    return get_path("count_report")


def get_figures_path() -> Path:
    """Get path to figures directory."""
    return get_path("data_figures")


def get_interpretability_path() -> Path:
    """Get path to interpretability directory."""
    return get_path("data_interpretability")


def get_astm_tolerance_config_path() -> Path:
    """Get path to ASTM tolerance config."""
    return get_path("astm_tolerance_config")


def get_verified_datasets_config_path() -> Path:
    """Get path to verified datasets config."""
    return get_path("verified_datasets_config")


def save_config(config: Optional[ProjectConfig] = None, 
               path: Optional[Path] = None) -> Path:
    """Save configuration to YAML."""
    return _config_manager.save_config(config, path)


def update_config(key: str, value: Any) -> None:
    """
    Update a single configuration value.
    
    Args:
        key: Configuration key to update.
        value: New value.
    """
    config = get_config()
    config_dict = config.to_dict()
    
    if key not in config_dict:
        raise CorrosionPipelineError(f"Configuration key '{key}' not found")
    
    setattr(config, key, value)
    _config_manager._config = config
    logger.info(f"Updated config: {key} = {value}")
