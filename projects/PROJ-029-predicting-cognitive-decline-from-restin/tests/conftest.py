"""
Pytest configuration and fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to the path if not already there
# This ensures imports like `from utils.graph import ...` work correctly
@pytest.fixture(autouse=True)
def setup_project_path():
    project_root = Path(__file__).parent.parent
    if str(project_root / "code") not in sys.path:
        sys.path.insert(0, str(project_root / "code"))
    yield
    # Cleanup if necessary (usually not needed for path)

# Optional: Add a fixture for temporary directory if needed, 
# though tmp_path is built-in.
# This file can be extended for more complex fixtures in the future.