"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import logging
from pathlib import Path
import pytest

# Add the 'code' directory to the path so we can import from src
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add the src directory to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Cleanup not strictly necessary as sys.path is process-local,
    # but good practice to keep state clean if tests are reloaded.
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests to capture output."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    yield