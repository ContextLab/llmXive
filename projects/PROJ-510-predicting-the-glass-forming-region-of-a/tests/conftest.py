"""
Pytest configuration and fixtures.
"""
import pytest
import os
import sys

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture
def sample_data(project_root):
    """Create a small sample dataframe for testing."""
    import pandas as pd
    import numpy as np
    np.random.seed(42)
    data = {
        'composition': ['Cu50Zr50', 'Cu60Zr30Al10', 'Fe40Ni40P20'],
        'critical_cooling_rate': [10.0, 20.0, 5.0]
    }
    return pd.DataFrame(data)
