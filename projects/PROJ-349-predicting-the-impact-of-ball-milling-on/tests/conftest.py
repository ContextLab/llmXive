"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def sample_experiment():
    """Fixture for a sample experiment record"""
    return {
        'experiment_id': 'exp_001',
        'source': 'Materials Project',
        'material_type': 'ceramic',
        'milling_speed': 300.0,
        'milling_time': 2.0,
        'ball_to_powder_ratio': 10.0,
        'Young\'s modulus': 200.0,
        'density': 5.0,
        'process_duration': 2.0,
        'D10': 10.0,
        'D50': 50.0,
        'D90': 90.0,
        'unstructured_flag': False
    }

@pytest.fixture
def tmp_data_dir(tmp_path):
    """Fixture for temporary data directory"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir