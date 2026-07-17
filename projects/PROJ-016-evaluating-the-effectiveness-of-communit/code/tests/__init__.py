"""
Test package initialization for llmXive project.
Provides pytest fixtures and test discovery configuration.
"""
import pytest
import sys
from pathlib import Path

# Ensure the code directory is in the Python path for imports
# This allows tests to import modules like `from config import get_config`
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary (though usually not needed for path insertion)
