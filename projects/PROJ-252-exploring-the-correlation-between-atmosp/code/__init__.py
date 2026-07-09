"""
llmXive Research Project - Code Package

This package contains the implementation modules for the atmospheric pressure
and earthquake precursor correlation study.
"""

from .config import Config
from .utils.logging import setup_logging, get_logger

__version__ = "0.1.0"
__all__ = ["Config", "setup_logging", "get_logger"]