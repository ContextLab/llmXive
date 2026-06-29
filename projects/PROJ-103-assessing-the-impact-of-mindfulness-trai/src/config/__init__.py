"""Configuration module for mindfulness-DMN connectivity study."""

from .settings import (
    Config,
    DatasetPaths,
    PreprocessingParams,
    MotionThresholds,
    StatisticalThresholds,
    load_config,
    save_config,
    get_default_config,
    validate_config,
)

__all__ = [
    "Config",
    "DatasetPaths",
    "PreprocessingParams",
    "MotionThresholds",
    "StatisticalThresholds",
    "load_config",
    "save_config",
    "get_default_config",
    "validate_config",
]
