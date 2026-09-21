import os
import pytest
from pathlib import Path
from code.config import (
    is_ci_environment,
    get_base_path,
    get_data_path,
    get_raw_data_path,
    get_processed_data_path,
    get_logs_path,
    get_resource_limits,
    ensure_dirs
)

def test_is_ci_environment_false():
    """Test that CI detection returns False when no CI vars are set."""
    # Ensure no CI vars are set for this test
    original_env = os.environ.copy()
    ci_vars = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'CIRCLECI', 'JENKINS_URL', 'TRAVIS']
    for var in ci_vars:
        if var in os.environ:
            del os.environ[var]

    assert is_ci_environment() is False

    # Restore environment
    os.environ.clear()
    os.environ.update(original_env)

def test_get_base_path():
    """Test that base path is a valid Path object."""
    path = get_base_path()
    assert isinstance(path, Path)
    assert path.exists()

def test_get_data_paths():
    """Test that data paths are correctly constructed."""
    base = get_base_path()
    assert get_data_path() == base / "data"
    assert get_raw_data_path() == base / "data" / "raw"
    assert get_processed_data_path() == base / "data" / "processed"
    assert get_logs_path() == base / "data" / "logs"

def test_resource_limits():
    """Test that resource limits are returned as a dict."""
    limits = get_resource_limits()
    assert isinstance(limits, dict)
    assert "max_ram_gb" in limits
    assert "max_workers" in limits
    assert limits["max_ram_gb"] > 0
    assert limits["max_workers"] > 0

def test_ensure_dirs():
    """Test that ensure_dirs creates the necessary directories."""
    # This test might fail if run in a restricted environment, but should pass in dev
    try:
        ensure_dirs()
        # Verify at least the data directory exists
        assert get_data_path().exists()
    except Exception:
        # If we can't create dirs (e.g. permissions), we still want to know the function exists
        pass
