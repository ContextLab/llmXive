"""
Configuration management for the exoplanet gap analysis pipeline.

This module provides centralized configuration loading and validation,
supporting both YAML configuration files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PipelineConfig:
    """
    Centralized configuration container for the pipeline.

    Attributes:
        data_dir: Base directory for all data files.
        raw_data_dir: Directory for raw downloaded data.
        processed_data_dir: Directory for processed/analyzed data.
        log_dir: Directory for log files.
        cache_dir: Directory for cached API responses.
        api_timeout: Timeout in seconds for external API calls.
        max_retries: Maximum number of retry attempts for failed API calls.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        parallel_workers: Number of parallel workers for data processing.
        enable_cache: Whether to enable API response caching.
    """
    data_dir: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    log_dir: str = "data/logs"
    cache_dir: str = "data/cache"
    api_timeout: int = 60
    max_retries: int = 3
    log_level: str = "INFO"
    parallel_workers: int = 4
    enable_cache: bool = True

    # Analysis specific
    period_max_days: float = 100.0
    radius_uncertainty_threshold: float = 0.20
    period_uncertainty_threshold: float = 0.01
    min_bin_size: int = 30
    gmm_components: int = 2
    bootstrap_iterations: int = 100
    outlier_std_threshold: float = 3.0

    # Theory comparison
    bonferroni_alpha: float = 0.025
    max_pipeline_runtime_hours: float = 6.0


def load_config(config_path: Optional[str] = None) -> PipelineConfig:
    """
    Load pipeline configuration from a YAML file or environment variables.

    Priority:
        1. Explicit config file path (if provided)
        2. Environment variable PIPELINE_CONFIG_PATH
        3. Default path: code/theory/config.yaml

    Args:
        config_path: Optional path to configuration file.

    Returns:
        PipelineConfig instance with loaded values.
    """
    config = PipelineConfig()

    # Determine config file path
    if config_path is None:
        config_path = os.getenv("PIPELINE_CONFIG_PATH")

    if config_path is None:
        # Default location relative to project root
        default_config_path = Path(__file__).parent.parent / "theory" / "config.yaml"
        if default_config_path.exists():
            config_path = str(default_config_path)
        else:
            # No config file found, return defaults
            return config

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")

    # Update config with values from YAML
    _update_config_from_dict(config, yaml_config)

    # Override with environment variables (if set)
    _update_config_from_env(config)

    return config


def _update_config_from_dict(config: PipelineConfig, data: Dict[str, Any]) -> None:
    """
    Update PipelineConfig fields from a dictionary.

    Args:
        config: Config instance to update.
        data: Dictionary of configuration values.
    """
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)


def _update_config_from_env(config: PipelineConfig) -> None:
    """
    Update PipelineConfig fields from environment variables.

    Environment variables are prefixed with PIPELINE_.
    Example: PIPELINE_API_TIMEOUT=120

    Args:
        config: Config instance to update.
    """
    env_mapping = {
        "DATA_DIR": "data_dir",
        "RAW_DATA_DIR": "raw_data_dir",
        "PROCESSED_DATA_DIR": "processed_data_dir",
        "LOG_DIR": "log_dir",
        "CACHE_DIR": "cache_dir",
        "API_TIMEOUT": "api_timeout",
        "MAX_RETRIES": "max_retries",
        "LOG_LEVEL": "log_level",
        "PARALLEL_WORKERS": "parallel_workers",
        "ENABLE_CACHE": "enable_cache",
        "PERIOD_MAX_DAYS": "period_max_days",
        "RADIUS_UNCERTAINTY_THRESHOLD": "radius_uncertainty_threshold",
        "PERIOD_UNCERTAINTY_THRESHOLD": "period_uncertainty_threshold",
        "MIN_BIN_SIZE": "min_bin_size",
        "GMM_COMPONENTS": "gmm_components",
        "BOOTSTRAP_ITERATIONS": "bootstrap_iterations",
        "OUTLIER_STD_THRESHOLD": "outlier_std_threshold",
        "BONFERRONI_ALPHA": "bonferroni_alpha",
        "MAX_PIPELINE_RUNTIME_HOURS": "max_pipeline_runtime_hours",
    }

    for env_key, config_attr in env_mapping.items():
        env_value = os.getenv(f"PIPELINE_{env_key}")
        if env_value is not None:
            try:
                # Determine type based on default value
                default_val = getattr(config, config_attr)
                if isinstance(default_val, bool):
                    setattr(config, config_attr, env_value.lower() in ("true", "1", "yes"))
                elif isinstance(default_val, int):
                    setattr(config, config_attr, int(env_value))
                elif isinstance(default_val, float):
                    setattr(config, config_attr, float(env_value))
                else:
                    setattr(config, config_attr, env_value)
            except ValueError:
                # Ignore invalid conversions, keep default
                pass


def get_config() -> PipelineConfig:
    """
    Get the global pipeline configuration (singleton pattern).

    Returns:
        PipelineConfig instance.
    """
    if not hasattr(get_config, "_config"):
        get_config._config = load_config()
    return get_config._config


def reset_config() -> None:
    """
    Reset the global configuration cache.

    Useful for testing or re-loading configuration.
    """
    if hasattr(get_config, "_config"):
        del get_config._config
