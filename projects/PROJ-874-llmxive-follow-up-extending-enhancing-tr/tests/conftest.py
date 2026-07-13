"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path if running from within the project
# This ensures imports like `from code.utils.video import ...` work correctly
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    # Determine the project root relative to this file
    # Assuming this file is at: projects/PROJ-.../tests/conftest.py
    # Root is: projects/PROJ-.../
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    yield
    
    # Cleanup if necessary (usually not needed for path insertion)
    pass