"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def pytest_configure(config):
    """Add custom markers if needed."""
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test."
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test."
    )
