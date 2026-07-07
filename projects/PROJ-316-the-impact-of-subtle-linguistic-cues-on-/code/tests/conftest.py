"""
Pytest configuration and shared fixtures.
This file ensures pytest can discover tests in the tests/ directory
and sets up basic configuration for linting/formatting checks.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import code/ modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def pytest_configure(config):
    """Configure pytest with project-specific settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
