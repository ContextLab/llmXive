"""
Unit tests for directory setup functionality.
"""
import os
import pytest
from pathlib import Path
from code.setup_directories import setup_directories

def test_setup_creates_directories():
    """Verify that setup_directories creates the required folder structure."""
    # Run the setup
    setup_directories()
    
    # Check existence of required directories
    root = Path(".")
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created."
        assert full_path.is_dir(), f"Path {dir_path} exists but is not a directory."