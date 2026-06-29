"""
Pytest configuration and fixtures for the llmXive research pipeline.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import numpy as np

# Ensure the project root is in the path for imports
# Assumes this file is at tests/conftest.py and root is parent of tests/
ROOT_DIR = Path(__file__).resolve().parent.parent
CODE_DIR = ROOT_DIR / "code"
DATA_DIR = ROOT_DIR / "data"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Configure logging for tests to avoid noise but allow debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the root directory of the project."""
    return ROOT_DIR

@pytest.fixture(scope="session")
def code_dir() -> Path:
    """Returns the path to the code directory."""
    return CODE_DIR

@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Returns the path to the data directory."""
    return DATA_DIR

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """
    Creates a temporary directory mimicking the project's data structure.
    Useful for tests that need to write/read files without polluting the real data folder.
    """
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    return tmp_path

@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Provides a minimal valid configuration dictionary for testing."""
    return {
        "seeds": {
            "random": 42,
            "numpy": 42
        },
        "paths": {
            "raw_data": str(DATA_DIR / "raw"),
            "processed_data": str(DATA_DIR / "processed")
        },
        "pipeline": {
            "filter_low": 1.0,
            "filter_high": 40.0,
            "notch_freq": 50.0,
            "epoch_tmin": -1.0,
            "epoch_tmax": 1.0
        }
    }

@pytest.fixture
def sample_electrode_positions() -> Dict[str, np.ndarray]:
    """
    Returns a dictionary of electrode names to 3D coordinates (x, y, z).
    Includes standard EEG positions used in the project.
    """
    return {
        "F3": np.array([-0.03, 0.06, 0.09]),
        "Fz": np.array([0.00, 0.06, 0.10]),
        "F4": np.array([0.03, 0.06, 0.09]),
        "P3": np.array([-0.03, -0.06, 0.08]),
        "Pz": np.array([0.00, -0.06, 0.09]),
        "P4": np.array([0.03, -0.06, 0.08]),
        "EOG_L": np.array([-0.10, 0.00, 0.00]),
        "EOG_R": np.array([0.10, 0.00, 0.00])
    }

@pytest.fixture
def mock_epochs_data() -> np.ndarray:
    """
    Generates a mock 3D numpy array representing EEG epochs.
    Shape: (n_epochs, n_channels, n_times)
    """
    n_epochs = 50
    n_channels = 6
    n_times = 256  # 1 second at 256 Hz
    data = np.random.randn(n_epochs, n_channels, n_times)
    # Add a small signal component to make it realistic
    signal = np.sin(np.linspace(0, 4 * np.pi, n_times)) * 0.1
    data[:, :, :] += signal[np.newaxis, np.newaxis, :]
    return data

@pytest.fixture
def mock_events() -> np.ndarray:
    """
    Generates a mock events array for MNE-style epoching.
    Shape: (n_events, 3) where columns are [sample, prev_value, event_id]
    """
    n_events = 50
    samples = np.sort(np.random.randint(100, 1000, n_events))
    events = np.column_stack([samples, np.zeros(n_events, dtype=int), np.ones(n_events, dtype=int)])
    return events

@pytest.fixture(autouse=True)
def setup_environment(monkeypatch, tmp_path):
    """
    Automatically sets environment variables for test isolation if needed.
    """
    # Example: Ensure we don't accidentally hit a real network or large dataset
    monkeypatch.setenv("TEST_MODE", "true")
    yield