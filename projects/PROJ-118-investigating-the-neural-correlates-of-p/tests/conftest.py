"""
Pytest configuration and fixtures for PROJ-118.

This file configures the pytest environment, providing shared fixtures
for project paths, configuration loading, and test data validation.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
# Assumes running from project root or tests/ directory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import project utilities to ensure they are available for tests
try:
    from code.data_utils import load_config_and_validate, get_subject_ids
    from code.config import CONFIG_PATH
except ImportError:
    # Fallback if config module structure differs slightly during early setup
    pass


@pytest.fixture(scope="session")
def project_root_path():
    """Return the root path of the project."""
    return project_root


@pytest.fixture(scope="session")
def data_raw_path(project_root_path):
    """Return the path to the raw data directory."""
    return project_root_path / "data" / "raw"


@pytest.fixture(scope="session")
def data_processed_path(project_root_path):
    """Return the path to the processed data directory."""
    return project_root_path / "data" / "processed"


@pytest.fixture(scope="session")
def results_path(project_root_path):
    """Return the path to the results directory."""
    return project_root_path / "results"


@pytest.fixture(scope="session")
def code_path(project_root_path):
    """Return the path to the code directory."""
    return project_root_path / "code"


@pytest.fixture(scope="session")
def config_path(project_root_path):
    """Return the path to the configuration file."""
    return project_root_path / "code" / "config.yaml"


@pytest.fixture(scope="session")
def valid_config(config_path):
    """
    Load and validate the project configuration.
    Returns the config dict if valid, otherwise skips the test.
    """
    if not config_path.exists():
        pytest.skip(f"Configuration file not found at {config_path}")

    try:
        config = load_config_and_validate(config_path)
        return config
    except Exception as e:
        pytest.fail(f"Failed to load or validate config: {e}")


@pytest.fixture(scope="session")
def subject_ids(valid_config, data_raw_path):
    """
    Return a list of valid subject IDs based on the raw data present.
    If no raw data is found, returns an empty list.
    """
    try:
        ids = get_subject_ids(data_raw_path)
        return ids
    except Exception:
        return []


@pytest.fixture(scope="session")
def has_raw_data(data_raw_path):
    """Check if raw data directory exists and is not empty."""
    return data_raw_path.exists() and any(data_raw_path.iterdir())


@pytest.fixture(scope="session")
def has_processed_data(data_processed_path):
    """Check if processed data directory exists and is not empty."""
    return data_processed_path.exists() and any(data_processed_path.iterdir())


@pytest.fixture(autouse=True)
def ensure_directories(project_root_path):
    """
    Ensure required directories exist before tests run.
    This is an autouse fixture to guarantee structure integrity.
    """
    dirs = [
        project_root_path / "data" / "raw",
        project_root_path / "data" / "processed",
        project_root_path / "results",
        project_root_path / "results" / "plots",
        project_root_path / "code",
        project_root_path / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)