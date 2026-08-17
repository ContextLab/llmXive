import pytest
import os
from config import Config, get_config, set_config, reset_config, load_config_from_env

def test_config_loading():
    """
    Verify that the Config dataclass contains the required fields with correct defaults.
    This test validates T009 requirements:
    - CPU_ONLY=True
    - EPSILON_FLOOR=1e-6
    - RANDOM_SEED (default 42)
    - NUM_MATRICES=10000
    - SIMULATION_STEPS=1000
    - NUM_RUNS=30
    """
    # Reset config to ensure fresh defaults
    reset_config()
    
    # Get the default configuration
    config = get_config()
    
    # Verify required fields and defaults
    assert config.CPU_ONLY is True, "CPU_ONLY should default to True"
    assert config.EPSILON_FLOOR == 1e-6, "EPSILON_FLOOR should default to 1e-6"
    assert config.RANDOM_SEED == 42, "RANDOM_SEED should default to 42"
    assert config.NUM_MATRICES == 10000, "NUM_MATRICES should default to 10000"
    assert config.SIMULATION_STEPS == 1000, "SIMULATION_STEPS should default to 1000"
    assert config.NUM_RUNS == 30, "NUM_RUNS should default to 30"
    
    # Verify other fields exist and have expected types
    assert isinstance(config.BATCH_SIZE, int)
    assert isinstance(config.LEARNING_RATE, float)
    assert isinstance(config.EPSILON_SWEEP_VALUES, list)
    assert len(config.EPSILON_SWEEP_VALUES) > 0

def test_config_env_override():
    """
    Verify that environment variables correctly override default configuration.
    """
    # Set specific environment variables
    os.environ['CPU_ONLY'] = 'false'
    os.environ['EPSILON_FLOOR'] = '1e-5'
    os.environ['RANDOM_SEED'] = '123'
    os.environ['NUM_MATRICES'] = '5000'
    os.environ['SIMULATION_STEPS'] = '500'
    os.environ['NUM_RUNS'] = '15'
    
    # Reset and reload config
    reset_config()
    config = get_config()
    
    # Verify overrides
    assert config.CPU_ONLY is False
    assert config.EPSILON_FLOOR == 1e-5
    assert config.RANDOM_SEED == 123
    assert config.NUM_MATRICES == 5000
    assert config.SIMULATION_STEPS == 500
    assert config.NUM_RUNS == 15
    
    # Clean up environment
    del os.environ['CPU_ONLY']
    del os.environ['EPSILON_FLOOR']
    del os.environ['RANDOM_SEED']
    del os.environ['NUM_MATRICES']
    del os.environ['SIMULATION_STEPS']
    del os.environ['NUM_RUNS']
    
    # Reset to defaults
    reset_config()