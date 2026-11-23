"""
Pytest configuration and fixtures for llmXive project.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def project_root():
    return PROJECT_ROOT

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provides a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_config(project_root, temp_output_dir):
    """Provides a sample configuration for testing."""
    from src.config import get_config
    config = get_config()
    config.output_dir = str(temp_output_dir)
    config.duration_steps = 10
    config.random_seed = 42
    config.memory_limit_mb = 512
    config.timeout_seconds = 60
    return config

@pytest.fixture
def sample_eco_director(sample_config):
    """Provides a configured EcoDirector instance."""
    from src.sim.eco_director import EcoDirector
    from src.sim.physics_oracle import PhysicsOracle
    
    oracle = PhysicsOracle()
    director = EcoDirector(config=sample_config, physics_oracle=oracle)
    return director
