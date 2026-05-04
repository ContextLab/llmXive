"""
Pytest configuration and shared fixtures for all tests.
"""
import pytest
from pathlib import Path
import numpy as np
from datetime import datetime
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def project_root():
    """Return project root path."""
    return PROJECT_ROOT

@pytest.fixture
def sample_timeseries():
    """Generate sample time series data for testing."""
    np.random.seed(42)
    n_points = 1000
    t = np.linspace(0, 10, n_points)
    
    # Base signal with trend and seasonality
    signal = (
        np.sin(2 * np.pi * t) +  # Seasonality
        0.1 * t +  # Trend
        np.random.normal(0, 0.1, n_points)  # Noise
    )
    
    return {
        'timestamp': t,
        'value': signal,
        'is_anomaly': np.zeros(n_points, dtype=int)
    }

@pytest.fixture
def sample_anomalies(sample_timeseries):
    """Inject anomalies into sample time series."""
    data = sample_timeseries.copy()
    anomaly_indices = [100, 200, 300, 500, 700]
    
    for idx in anomaly_indices:
        data['value'][idx] += 5.0  # Point anomalies
        data['is_anomaly'][idx] = 1
    
    return data

@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory for test artifacts."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

@pytest.fixture
def mock_config():
    """Return mock configuration for testing."""
    return {
        'random_seed': 42,
        'max_components': 50,
        'convergence_threshold': 0.001,
        'max_iterations': 500,
        'alpha': 1.0,
        'beta': 0.1,
        'kappa': 1.0,
        'nu': 2
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup clean test environment before each test."""
    # Set numpy random seed for reproducibility
    np.random.seed(42)
    yield
    # Cleanup after test
