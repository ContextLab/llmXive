import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

@pytest.fixture
def sample_entropy_vector():
    """Provide a sample entropy vector for testing."""
    return np.array([0.5, 0.6, 0.55, 0.58, 0.62])

@pytest.fixture
def sample_subject_data():
    """Provide sample subject data for testing."""
    return pd.DataFrame({
        'subject_id': ['100307', '100408', '100509'],
        'age': [25, 28, 30],
        'sex': ['M', 'F', 'M'],
        'creative_score': [12.5, 14.2, 11.8]
    })

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_time_series():
    """Generate a mock fMRI time series for testing."""
    np.random.seed(42)
    return np.random.randn(100, 360)  # 100 time points, 360 parcels
