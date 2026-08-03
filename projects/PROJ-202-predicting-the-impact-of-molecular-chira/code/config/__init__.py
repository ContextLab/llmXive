"""
Configuration package for the molecular chirality pipeline.

Exports the global Config object and utility functions.
"""
from .settings import Config, config, PROJECT_ROOT, DEFAULT_DATA_DIR

__all__ = [
    "Config",
    "config",
    "PROJECT_ROOT",
    "DEFAULT_DATA_DIR"
]
