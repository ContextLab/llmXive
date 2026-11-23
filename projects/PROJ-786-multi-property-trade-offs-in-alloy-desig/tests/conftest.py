"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def pytest_configure(config):
    """Configure pytest."""
    pass
