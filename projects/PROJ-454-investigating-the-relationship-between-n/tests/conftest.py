"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# Optional: Setup global fixtures if needed
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "contract: mark test as a contract/schema validation test."
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test."
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test."
    )
