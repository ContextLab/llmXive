"""
Pytest configuration and fixtures.
"""
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_data():
    """Create sample crack propagation data for testing."""
    np.random.seed(42)
    n_samples = 100
    delta_k = np.random.uniform(5, 50, n_samples)
    da_dN = 10 ** (np.random.normal(0, 0.5, n_samples)) * (delta_k ** 2.5)
    
    return pd.DataFrame({
        'delta_K': delta_k,
        'da_dN': da_dN,
        'material': ['Al2024'] * n_samples,
        'heat_treatment': ['T3'] * n_samples
    })
