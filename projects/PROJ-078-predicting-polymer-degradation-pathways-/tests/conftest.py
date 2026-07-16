"""
Pytest configuration and shared fixtures for the polymer degradation pipeline.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Add the project root to sys.path to allow imports from code/
# This assumes the project is run from the root directory.
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Configure logging for tests to avoid silent failures
@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for all tests to capture output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    yield
