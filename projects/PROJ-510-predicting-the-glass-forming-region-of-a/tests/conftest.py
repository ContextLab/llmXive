"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import sys

# Ensure the code directory is in the path for imports during tests
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(__file__), '..', 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture
def sample_data():
    """Provide a sample dataframe for testing."""
    import pandas as pd
    return pd.DataFrame({
        'composition': ['Fe0.33Cr0.33Ni0.34', 'Fe0.5Cr0.5', 'Ni0.5Cu0.5'],
        'critical_cooling_rate': [100.0, 50.0, 200.0],
        'mixing_enthalpy': [-10.0, -5.0, -2.0],
        'atomic_size_mismatch': [0.05, 0.02, 0.01],
        'electronegativity_variance': [0.001, 0.0005, 0.0002]
    })