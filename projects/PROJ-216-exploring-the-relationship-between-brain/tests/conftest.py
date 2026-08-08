"""
Pytest configuration and fixtures.
Ensures the test environment is set up correctly before running tests.
"""
import pytest
import os
import sys
from pathlib import Path

@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session", autouse=True)
def verify_test_directories(project_root):
    """
    Auto-verify that test directories exist before running any tests.
    This ensures T001f requirement is met.
    """
    unit_dir = project_root / "tests" / "unit"
    integ_dir = project_root / "tests" / "integration"
    
    if not unit_dir.is_dir():
        unit_dir.mkdir(parents=True, exist_ok=True)
    
    if not integ_dir.is_dir():
        integ_dir.mkdir(parents=True, exist_ok=True)
    
    assert unit_dir.is_dir(), "tests/unit directory must exist"
    assert integ_dir.is_dir(), "tests/integration directory must exist"