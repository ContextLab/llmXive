"""
Simple smoke test to verify pytest configuration and directory structure.
This ensures T006 is successfully completed.
"""
import os
from pathlib import Path

import pytest


def test_project_root_accessible():
    """Verify that the project root is in sys.path."""
    import sys
    project_root = Path(__file__).parent.parent
    assert str(project_root) in sys.path, "Project root not in sys.path"


def test_directory_structure_exists(project_root):
    """Verify that the required test directories exist."""
    required_dirs = [
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"


def test_conftest_imports_fixtures():
    """Verify that fixtures defined in conftest are discoverable."""
    # This test will fail if conftest.py is missing or broken
    from code.conftest import temp_data_dir, setup_test_logging
    assert temp_data_dir is not None
    assert setup_test_logging is not None


def test_temp_data_dir_fixture(temp_data_dir):
    """Verify the temp_data_dir fixture creates the expected structure."""
    assert temp_data_dir.exists()
    assert (temp_data_dir / "raw").exists()
    assert (temp_data_dir / "processed").exists()
    assert (temp_data_dir / "figures").exists()

def test_logging_fixture_logs(caplog):
    """Verify that the logging fixture captures logs."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Test log message")
    assert "Test log message" in caplog.text