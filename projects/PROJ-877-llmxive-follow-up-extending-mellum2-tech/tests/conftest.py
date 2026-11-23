"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path for imports
# This assumes tests are run from the project root:
# python -m pytest
@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_path():
    """Ensure the code directory is in the Python path for testing."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Ensure data directories exist for tests
    data_dir = project_root / "data"
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (data_dir / "results").mkdir(parents=True, exist_ok=True)

    yield
