"""
llmXive Research Pipeline - Code Package

This package contains the core implementation for the temporal discounting
and procrastination research pipeline.
"""

from .config import get_config, PROJECT_ROOT, CONFIG_PATH

__all__ = [
    "get_config",
    "PROJECT_ROOT",
    "CONFIG_PATH",
]

__version__ = "0.1.0"
