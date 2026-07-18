"""
Pytest configuration and shared fixtures for the sensitivity tests.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

@pytest.fixture
def sample_eeg_data():
    """Generate a sample EEG time-series for testing."""
    # 100 timepoints x 64 channels (typical EEG setup)
    return np.random.randn(100, 64)

@pytest.fixture
def sample_avalanche_events():
    """Generate sample avalanche events for testing."""
    return [
        {"size": 5, "duration": 2, "timestamp": 100},
        {"size": 3, "duration": 1, "timestamp": 150},
        {"size": 8, "duration": 3, "timestamp": 200}
    ]

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "sensitivity_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir