"""
Code package initialization for PROJ-273.
Exposes setup utilities for project structure management.
"""
from .setup_project_structure import create_directory_structure
from .setup_data_dirs import setup_data_directories

__all__ = [
    "create_directory_structure",
    "setup_data_directories"
]
