"""
Initialization file for the code package.

This file ensures that the code directory is recognized as a Python package
and allows for relative imports within the package.
"""
__version__ = "0.1.0"
__author__ = "llmXive Research Team"
__description__ = "Statistical Discrepancies in Publicly Available Election Data"

# Import key modules for easy access
from .setup_data_directories import setup_data_directories
from .logger import setup_logging, get_logger
from .models import Discrepancy, Jurisdiction
from .utils.hashing import compute_file_hash, save_checksums

__all__ = [
    'setup_data_directories',
    'setup_logging',
    'get_logger',
    'Discrepancy',
    'Jurisdiction',
    'compute_file_hash',
    'save_checksums'
]
