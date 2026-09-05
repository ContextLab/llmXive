"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports from code/
# Assumes tests/ is at projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/
# and code/ is at projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add the project root to sys.path for imports."""
    # Determine the project root relative to this file
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup not strictly necessary but good practice
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))
