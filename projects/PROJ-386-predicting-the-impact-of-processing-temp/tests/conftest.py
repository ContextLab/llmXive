"""
Pytest configuration and fixtures for the project.
Ensures the project structure exists before tests run.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def ensure_project_structure():
    """
    Automatically create required directories before running tests.
    This ensures tests can run even if setup_structure.py hasn't been run manually.
    """
    root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "state"
    ]

    for dir_name in required_dirs:
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    yield
    # Teardown logic if needed
