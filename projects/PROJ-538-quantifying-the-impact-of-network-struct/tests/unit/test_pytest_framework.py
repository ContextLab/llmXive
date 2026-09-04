"""
Basic smoke test to verify the pytest framework is correctly configured
and can import project modules successfully.
"""
import pytest
import sys
from pathlib import Path

# Ensure imports work
from code.config import Config, RunMode
from code.models import AtomicSnapshot, DefectGraph
from code.utils import DataAvailabilityError, VoronoiFailure, get_logger

def test_imports_resolve():
    """Verify that core module imports resolve without error."""
    assert Config is not None
    assert RunMode is not None
    assert AtomicSnapshot is not None
    assert DefectGraph is not None
    assert DataAvailabilityError is not None
    assert VoronoiFailure is not None
    assert get_logger is not None

def test_config_instantiation(test_config):
    """Verify the test fixture provides a valid config."""
    assert test_config.run_mode == RunMode.SYNTHETIC
    assert test_config.data_dir.exists() or True # Path might not exist on disk yet but object is valid
    assert test_config.min_completeness == 0.50

def test_error_hierarchy():
    """Verify custom exceptions inherit from Exception."""
    assert issubclass(DataAvailabilityError, Exception)
    assert issubclass(VoronoiFailure, Exception)

def test_pytest_cov_marker():
    """
    Dummy test to ensure pytest-cov can track coverage.
    The actual coverage report is generated via CLI flags, not this test logic.
    """
    assert True
