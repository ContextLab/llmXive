import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_root_path():
    return project_root

@pytest.fixture
def sample_dataframe():
    """Create a minimal valid DataFrame for testing."""
    import pandas as pd
    import numpy as np
    
    data = {
        'game_id': range(10),
        'year': [2019] * 10,
        'team_id': ['LAA'] * 10,
        'opponent_id': ['BOS'] * 10,
        'home_runs': np.random.randint(0, 5, 10),
        'hits': np.random.randint(5, 15, 10),
        'runs': np.random.randint(0, 10, 10),
        'era': np.random.uniform(2.0, 6.0, 10),
        'avg': np.random.uniform(0.200, 0.350, 10),
        'woba': np.random.uniform(0.300, 0.400, 10),
        'babip': np.random.uniform(0.250, 0.350, 10),
        'park_factor': np.random.uniform(0.9, 1.1, 10),
        'run_expectancy': np.random.uniform(0.0, 2.0, 10),
        'is_win': np.random.randint(0, 2, 10)
    }
    return pd.DataFrame(data)

@pytest.fixture(autouse=True)
def setup_env():
    """Ensure required environment variables are set for tests."""
    os.environ['RANDOM_SEED'] = '42'
    os.environ['CI_MODE'] = 'true'
    yield
    # Cleanup if needed
