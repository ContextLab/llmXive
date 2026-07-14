"""
Pytest configuration and fixtures for the project.

This file sets up the test environment, ensuring that the project root
is in the Python path and that necessary fixtures are available.
"""
import sys
import os
from pathlib import Path

# Add the project root to the path so we can import from code/
# This is crucial for tests that import modules like `code.utils.metrics`
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Optional: Define fixtures for common test data or mocks
# Example:
# @pytest.fixture
# def sample_repo_data():
#     return {"name": "test-repo", "language": "Python"}

def pytest_configure(config):
    """
    Configure pytest markers or settings.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring network access"
    )
