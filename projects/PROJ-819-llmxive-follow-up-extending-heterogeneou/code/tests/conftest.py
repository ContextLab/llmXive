"""
Pytest configuration and fixtures for llmXive project.
"""
import pytest
import sys
import os
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield

@pytest.fixture
def benchmark_data_dir(tmp_path):
    """Fixture providing a temporary directory for benchmark data."""
    data_dir = tmp_path / "data" / "derived"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def sample_cache_dir(tmp_path):
    """Fixture providing a temporary directory for cache storage."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def pytest_configure(config):
    """
    Global pytest configuration hook.
    Ensures pytest-benchmark is available if requested, though it is
    optional for basic tests.
    """
    # No global configuration changes needed beyond path setup in fixtures
    pass
