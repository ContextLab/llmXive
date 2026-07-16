"""
Pytest configuration and fixtures for the llmXive automated science pipeline.

This file configures the pytest environment and provides shared fixtures
for testing the EEG preprocessing and analysis pipeline.
"""
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import yaml

# Add the project root to the path to allow imports from code/
# This assumes tests/ is at the root level alongside code/
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root path of the project."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Return the path to the data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def raw_data_dir(data_dir: Path) -> Path:
    """Return the path to the raw data directory."""
    return data_dir / "raw"


@pytest.fixture(scope="session")
def processed_data_dir(data_dir: Path) -> Path:
    """Return the path to the processed data directory."""
    return data_dir / "processed"


@pytest.fixture(scope="session")
def results_dir(project_root: Path) -> Path:
    """Return the path to the results directory."""
    return project_root / "results"


@pytest.fixture(scope="function")
def temp_output_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs that is cleaned up after."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="session")
def config_path(project_root: Path) -> Path:
    """Return the path to the configuration file."""
    return project_root / "code" / "config.yaml"


@pytest.fixture(scope="function")
def sample_config(config_path: Path) -> Dict[str, Any]:
    """
    Load the sample configuration from code/config.yaml.
    Falls back to a minimal valid config if the file doesn't exist yet
    (useful for early-stage testing before T005 is fully populated).
    """
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    # Fallback minimal config for testing purposes if file is missing
    # This mirrors the expected schema from T005
    return {
        "filter": {
            "lowcut": 1.0,
            "highcut": 30.0,
            "ftype": "fir"
        },
        "epoch": {
            "tmin": -0.2,
            "tmax": 0.6,
            "baseline": (None, 0)
        },
        "ica": {
            "threshold": 0.8,
            "method": "fastica"
        },
        "montage": {
            "standard": ["Fz", "FCz", "Cz", "Pz", "F3", "F4", "C3", "C4", "P3", "P4"]
        }
    }


@pytest.fixture(scope="function")
def mock_subject_id() -> str:
    """Return a mock subject ID for testing."""
    return "sub-01"


@pytest.fixture(scope="function")
def mock_event_id() -> Dict[str, int]:
    """Return a mock event ID mapping for EEG epochs."""
    return {
        "standard": 1,
        "deviant": 2
    }