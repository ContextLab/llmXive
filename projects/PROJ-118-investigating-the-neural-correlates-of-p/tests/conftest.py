"""
Pytest configuration and shared fixtures for PROJ-118.

This file configures the test environment, sets up temporary directories
for test artifacts, and provides fixtures for loading configuration
and accessing project paths.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any, Dict

import pytest
import yaml

# Add the project root to the path so imports work during tests
# Assumes tests are run from the project root: pytest tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root path of the project."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def code_dir(project_root: Path) -> Path:
    """Return the path to the code directory."""
    return project_root / "code"


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Return the path to the data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def results_dir(project_root: Path) -> Path:
    """Return the path to the results directory."""
    return project_root / "results"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test artifacts.
    Cleans up automatically after the test.
    """
    tmp = Path(tempfile.mkdtemp(prefix="llmxive_test_"))
    yield tmp
    if tmp.exists():
        shutil.rmtree(tmp)


@pytest.fixture
def sample_config(temp_dir: Path) -> Path:
    """
    Create a temporary config.yaml file with valid schema for testing.
    Returns the path to the created file.
    """
    config_data = {
        "pipeline": {
            "filter": {
                "lowcut": 1.0,
                "highcut": 30.0,
                "ftype": "iir"
            },
            "epoch": {
                "tmin": -0.2,
                "tmax": 0.6,
                "baseline": (None, 0)
            },
            "ica": {
                "threshold": 0.8,
                "method": "fastica"
            }
        },
        "paths": {
            "raw": str(temp_dir / "raw"),
            "processed": str(temp_dir / "processed")
        }
    }

    # Create directories
    (temp_dir / "raw").mkdir(parents=True, exist_ok=True)
    (temp_dir / "processed").mkdir(parents=True, exist_ok=True)

    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return config_path


@pytest.fixture
def load_config_fixture(sample_config: Path):
    """
    Fixture to load the sample config for testing config loading functions.
    Yields the loaded dictionary.
    """
    with open(sample_config, "r") as f:
        yield yaml.safe_load(f)


@pytest.fixture(autouse=True)
def setup_environment():
    """
    Autouse fixture to ensure environment variables are set correctly
    or mocked for testing if necessary.
    """
    # Ensure we are in the project root context
    os.chdir(PROJECT_ROOT)
    yield
    # Cleanup if needed
    pass