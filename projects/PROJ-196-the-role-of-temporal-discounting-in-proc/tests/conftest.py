"""
Pytest configuration and fixtures for llmXive research pipeline.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Add the project root to sys.path to allow relative imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing purposes."""
    np.random.seed(42)
    n = 100
    data = {
        'participant_id': range(1, n + 1),
        'discount_rate_k': np.random.lognormal(mean=0, sigma=1, size=n),
        'procrastination_score': np.random.normal(loc=50, scale=10, size=n),
        'wm_accuracy': np.random.normal(loc=0.8, scale=0.1, size=n),
        'wm_rt': np.random.normal(loc=500, scale=50, size=n),
        'age': np.random.randint(18, 65, size=n),
        'gender': np.random.choice(['M', 'F'], size=n),
        'education': np.random.randint(12, 20, size=n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
