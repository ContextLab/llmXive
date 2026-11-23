"""
Root package for the molecular polarity prediction pipeline.
This file ensures the code directory is treated as a Python package.
"""
from .utils.logging_config import setup_logging, get_logger

# Initialize logging when the package is imported
setup_logging()

__all__ = ["setup_logging", "get_logger"]
