"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

@pytest.fixture
def sample_eeg_data():
    """Fixture providing sample EEG data for testing."""
    import numpy as np
    # Create a small sample dataset
    n_channels = 10
    n_times = 1000
    data = np.random.randn(n_channels, n_times)
    times = np.linspace(0, 1, n_times)
    return {'data': data, 'times': times}

@pytest.fixture
def sample_trajectory_data():
    """Fixture providing sample trajectory data."""
    import pandas as pd
    df = pd.DataFrame({
        'time': [0.1, 0.2, 0.3],
        'x': [1.0, 1.1, 1.2],
        'y': [1.0, 1.1, 1.2],
        'heading_angle': [45.0, 46.0, 47.0]
    })
    return df

@pytest.fixture
def temp_output_dir(tmp_path):
    """Fixture providing a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir