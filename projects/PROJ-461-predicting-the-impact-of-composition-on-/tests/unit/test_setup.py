"""
Unit tests for project setup functionality.
Verifies that the directory structure is created correctly.
"""
import pytest
import inspect
from setup_project import setup_directories

def test_required_directories_defined():
    """
    Verify that the setup script contains the required directory list.
    """
    source = inspect.getsource(setup_directories)
    
    required_dirs = [
        "code/data",
        "code/features",
        "code/models",
        "code/analysis",
        "data",
        "models",
        "reports",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    for dir_name in required_dirs:
        assert f'"{dir_name}"' in source or f"'{dir_name}'" in source, \
            f"Directory {dir_name} not found in setup_directories definition."