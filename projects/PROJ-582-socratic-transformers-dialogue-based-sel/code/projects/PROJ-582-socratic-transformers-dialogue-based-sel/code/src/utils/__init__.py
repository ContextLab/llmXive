"""
Utilities package for Socratic Transformers project.

Provides logging, configuration, metrics, and model loading utilities.
"""

from .config import SocraticConfig, load_config_from_env, get_config, set_global_config, ensure_directories, init_project, merge_configs
from .logging import SocraticLogger, get_logger
from .metrics import compute_prediction_error_proxy, compute_calibration_error, compute_ngram_overlap, MetricCalculator
from .model_loader import load_model, get_model_card, validate_model_compatibility

__all__ = [
    "SocraticConfig",
    "load_config_from_env",
    "get_config",
    "set_global_config",
    "ensure_directories",
    "init_project",
    "merge_configs",
    "SocraticLogger",
    "get_logger",
    "compute_prediction_error_proxy",
    "compute_calibration_error",
    "compute_ngram_overlap",
    "MetricCalculator",
    "load_model",
    "get_model_card",
    "validate_model_compatibility",
]