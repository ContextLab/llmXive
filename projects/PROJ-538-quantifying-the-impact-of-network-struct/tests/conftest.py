"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
import sys
import os
from pathlib import Path

# Add the project root to the path to allow relative imports from code/
# This assumes the tests are run from the project root: python -m pytest
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config, RunMode
from code.utils import get_logger

@pytest.fixture(scope="session")
def test_config():
    """
    Provides a test-specific configuration object.
    Uses synthetic mode by default to avoid external API dependencies in unit tests.
    """
    cfg = Config(
        run_mode=RunMode.SYNTHETIC,
        data_dir=project_root / "data",
        output_dir=project_root / "data" / "processed",
        figures_dir=project_root / "figures",
        log_file=project_root / "data" / "audit_log_test.json",
        min_completeness=0.50,  # Lower threshold for testing
        seed=42
    )
    return cfg

@pytest.fixture
def test_logger(test_config):
    """
    Provides a logger instance configured for testing.
    """
    return get_logger("test_runner", log_file=str(test_config.log_file))

@pytest.fixture(autouse=True)
def reset_state():
    """
    Optional fixture to reset any global state between tests if needed.
    Currently a placeholder for future state management.
    """
    yield
    pass
