"""
Pytest configuration and fixtures for CPU-only execution.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path so imports work
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Add the project root to sys.path for imports."""
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    
    # Ensure code directory is explicitly importable
    code_dir = root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield

@pytest.fixture(scope="session", autouse=True)
def configure_cpu_only():
    """
    Force CPU-only execution environment for all tests.
    Disables GPU usage and sets memory limits.
    """
    # Explicitly set environment variables for CPU-only
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Set a reasonable memory limit for CI environments (approx 7GB as per spec)
    # This is a soft limit hint for the test runner
    os.environ["PYTEST_MAX_RAM_GB"] = "7"
    
    yield

@pytest.fixture
def sample_config(tmp_path):
    """Create a temporary config directory for tests."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir
