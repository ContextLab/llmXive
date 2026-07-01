"""
Data acquisition and generation module.
Contains scripts for downloading real data or generating synthetic datasets.
"""

# Public API for the data module
from .download_data import download_data
from .generate_synthetic_data import generate_synthetic_data

__all__ = ["download_data", "generate_synthetic_data"]
