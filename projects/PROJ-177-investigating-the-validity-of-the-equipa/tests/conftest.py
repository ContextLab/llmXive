"""
Pytest configuration and fixtures.
"""

import os
import sys
import random
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix random seed for reproducibility
@pytest.fixture(autouse=True)
def set_random_seed():
    """Set random seeds for reproducibility."""
    random.seed(42)
    np.random.seed(42)
    yield

@pytest.fixture
def sample_tracking_data():
    """Generate sample tracking data for tests."""
    data = {
        'particle_id': [1] * 10 + [2] * 10,
        'timestamp': list(np.linspace(0, 1, 10)) + list(np.linspace(0, 1, 10)),
        'x': np.random.rand(20),
        'y': np.random.rand(20),
        'z': np.random.rand(20),
        'theta': np.random.rand(20)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_driving_data():
    """Generate sample driving signal data."""
    data = {
        'timestamp': np.linspace(0, 1, 100),
        'frequency': 10.0 + 5.0 * np.sin(2 * np.pi * np.linspace(0, 1, 100)),
        'amplitude': 1.0
    }
    return pd.DataFrame(data)

@pytest.fixture
def config_fixture():
    """Load configuration for tests."""
    from config import load_config
    return load_config()

@pytest.fixture
def temp_raw_dir(tmp_path):
    """Create a temporary raw data directory with sample files."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    # Create sample tracking file
    tracking_file = raw_dir / "tracking_sample.csv"
    data = "particle_id,timestamp,x,y,z,theta\n1,0.0,0.0,0.0,0.0,0.0\n1,0.1,0.1,0.0,0.0,0.1"
    tracking_file.write_text(data)
    
    # Create sample driving file
    driving_file = raw_dir / "driving_sample.csv"
    data = "timestamp,frequency,amplitude\n0.0,10.0,1.0\n0.1,10.0,1.0"
    driving_file.write_text(data)
    
    return raw_dir
