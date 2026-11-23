"""
Pytest configuration and shared fixtures for the llmXive pipeline.
"""
import os
import sys
import logging
from pathlib import Path
import pytest

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for all tests to capture output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    yield
