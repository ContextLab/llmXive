"""
Pytest configuration and fixtures for the llmXive project.

This file ensures that the test environment is correctly set up,
particularly for contract tests that rely on project structure.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to sys.path to allow imports from src/ and other modules
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup not strictly necessary as sys.path is process-scoped

# Optional: Global timeout or fixture for resource-heavy tests could go here
# For now, keeping it minimal to support the contract test structure.