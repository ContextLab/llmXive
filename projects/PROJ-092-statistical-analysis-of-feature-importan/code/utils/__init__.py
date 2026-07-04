"""
Utility modules for the Statistical Analysis of Feature Importance Drift project.

This package provides:
- Config: Configuration management via dataclass and environment variables.
- Logger: Centralized logging setup and retrieval.
- StatsAggregator: Aggregation of stability metrics from processed windows.
"""
from .config import Config, get_config, reset_config, load_config_from_env
from .logger import setup_logger, get_logger
from .stats_aggregator import calculate_stability_metrics, aggregate_from_profiles, save_stability_report

__all__ = [
    "Config",
    "get_config",
    "reset_config",
    "load_config_from_env",
    "setup_logger",
    "get_logger",
    "calculate_stability_metrics",
    "aggregate_from_profiles",
    "save_stability_report",
]
