"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path for all tests
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add code directory to sys.path for all tests."""
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield
    
    # Cleanup if needed
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def sample_m_dwarf_data():
    """Provide sample M-dwarf data for testing."""
    import pandas as pd
    import numpy as np
    
    return pd.DataFrame({
        'star_id': [1, 2, 3],
        'spectral_type': ['M0', 'M3', 'M5'],
        'flare_count': [15, 20, 12],
        'mass': [0.5, 0.4, 0.3],
        'radius': [0.5, 0.4, 0.3],
        'semi_major_axis': [0.1, 0.15, 0.12],
        'system_age': [5.0, 6.0, 4.0]
    })

@pytest.fixture
def sample_exoplanet_data():
    """Provide sample exoplanet data for testing."""
    import pandas as pd
    
    return pd.DataFrame({
        'host_star_id': [1, 2, 3, 4],
        'mass': [0.5, 0.4, 0.3, 0.6],
        'radius': [0.5, 0.4, 0.3, 0.6],
        'semi_major_axis': [0.1, 0.15, 0.12, 0.2],
        'orbital_period': [5.0, 8.0, 6.0, 10.0]
    })

@pytest.fixture
def sample_flare_data():
    """Provide sample flare data for testing."""
    import pandas as pd
    
    return pd.DataFrame({
        'host_star_id': [1, 2, 3, 5],
        'flare_count': [15, 20, 12, 8],
        'total_energy': [1e30, 1.5e30, 1.2e30, 8e29]
    })
