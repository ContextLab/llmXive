"""
Data acquisition and generation modules.
"""
from .download_data import download_data
from .generate_synthetic_data import generate_synthetic_data, main

__all__ = ["download_data", "generate_synthetic_data", "main"]
