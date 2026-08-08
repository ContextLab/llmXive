"""Utilities package for the Socratic Transformers project."""
from .logging import SocraticJsonFormatter, SocraticLogger, get_logger
from .config import SocraticConfig, load_config_from_env, get_config, set_global_config, ensure_directories, init_project
from .metrics import MetricCalculator, compute_prediction_error_proxy, compute_calibration_error, compute_ngram_overlap
from .model_loader import load_model, get_model_card, validate_model_compatibility, main

__all__ = [
    "SocraticJsonFormatter",
    "SocraticLogger",
    "get_logger",
    "SocraticConfig",
    "load_config_from_env",
    "get_config",
    "set_global_config",
    "ensure_directories",
    "init_project",
    "MetricCalculator",
    "compute_prediction_error_proxy",
    "compute_calibration_error",
    "compute_ngram_overlap",
    "load_model",
    "get_model_card",
    "validate_model_compatibility",
    "main",
]
