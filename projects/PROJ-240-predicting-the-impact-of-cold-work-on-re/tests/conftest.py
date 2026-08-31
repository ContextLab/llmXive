import pytest
import pandas as pd
import numpy as np
from pathlib import Path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'cold_work': [10, 20, 30, 40, 50],
        'annealing_temp': [300, 350, 400, 450, 500],
        'Mn_content': [0.5, 0.6, 0.7, 0.8, 0.9],
        'Mg_content': [0.4, 0.5, 0.6, 0.7, 0.8],
        'Si_content': [0.2, 0.3, 0.4, 0.5, 0.6],
        'Cu_content': [0.1, 0.2, 0.3, 0.4, 0.5],
        'time_to_peak': [100.0, 90.0, 80.0, 70.0, 60.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path
