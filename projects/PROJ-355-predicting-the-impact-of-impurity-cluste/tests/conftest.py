"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports
@pytest.fixture(autouse=True)
def add_project_root():
    # Determine project root relative to this file
    current_dir = Path(__file__).parent.parent
    code_path = current_dir / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))