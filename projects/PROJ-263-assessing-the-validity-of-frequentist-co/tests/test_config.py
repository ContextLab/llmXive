import os
import json
import random
import numpy as np
import pytest
from pathlib import Path
import tempfile
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    load_config,
    get_random_seed,
    get_data_dir,
    get_output_dir,
    get_log_level,
    get_simulation_config,
    save_config,
    set_random_seed,
    initialize_random_state,
    DEFAULT_CONFIG
)

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_load_config_creates_default(temp_config_file):
    """Test that load_config creates a default config if file doesn't exist."""
    # Remove the file if it exists
    if os.path.exists(temp_config_file):
        os.remove(temp_config_file)

    config = load_config(temp_config_file)

    assert "random_seed" in config
    assert "data_dir" in config
    assert "output_dir" in config
    assert "simulation" in config
    assert config["random_seed"] == DEFAULT_CONFIG["random_seed"]

def test_load_config_loads_existing(temp_config_file):
    """Test that load_config loads an existing config."""
    test_config = {
        "random_seed": 12345,
        "data_dir": "custom_data",
        "output_dir": "custom_outputs",
        "log_level": "DEBUG",
        "simulation": {
            "num_replications": 5000
        }
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)

    assert config["random_seed"] == 12345
    assert config["data_dir"] == "custom_data"
    assert config["log_level"] == "DEBUG"
    # Default values should be filled for missing keys
    assert config["simulation"]["sample_sizes"] == DEFAULT_CONFIG["simulation"]["sample_sizes"]

def test_save_config(temp_config_file):
    """Test that save_config writes the config correctly."""
    test_config = {
        "random_seed": 99999,
        "data_dir": "test_data",
        "output_dir": "test_outputs",
        "log_level": "WARNING",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    save_config(test_config, temp_config_file)

    # Verify file exists
    assert os.path.exists(temp_config_file)

    # Verify content
    with open(temp_config_file, 'r') as f:
        loaded = json.load(f)

    assert loaded["random_seed"] == 99999
    assert loaded["data_dir"] == "test_data"

def test_get_random_seed(temp_config_file):
    """Test that get_random_seed returns the correct seed."""
    test_config = {
        "random_seed": 77777,
        "data_dir": "data",
        "output_dir": "outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    seed = get_random_seed(config)

    assert seed == 77777

def test_get_random_seed_default():
    """Test that get_random_seed returns default when not specified."""
    config = {
        "data_dir": "data",
        "output_dir": "outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    seed = get_random_seed(config)
    assert seed == DEFAULT_CONFIG["random_seed"]

def test_set_random_seed():
    """Test that set_random_seed actually sets the seed."""
    # Set seed to a specific value
    set_random_seed(42)

    # Generate some random numbers
    val1 = random.random()
    arr1 = np.random.random(5)

    # Reset seed to the same value
    set_random_seed(42)

    # Generate the same random numbers
    val2 = random.random()
    arr2 = np.random.random(5)

    # They should be identical
    assert val1 == val2
    np.testing.assert_array_equal(arr1, arr2)

def test_initialize_random_state(temp_config_file):
    """Test that initialize_random_state sets the seed correctly."""
    test_config = {
        "random_seed": 88888,
        "data_dir": "data",
        "output_dir": "outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    seed = initialize_random_state(config)

    assert seed == 88888

    # Verify randomness is deterministic
    val1 = random.random()
    val2 = random.random()

    # Re-initialize
    initialize_random_state(config)

    assert random.random() == val1
    assert random.random() == val2

def test_get_data_dir(temp_config_file):
    """Test that get_data_dir returns the correct path."""
    test_config = {
        "random_seed": 42,
        "data_dir": "my_data_dir",
        "output_dir": "outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    data_dir = get_data_dir(config)

    assert data_dir == "my_data_dir"

def test_get_output_dir(temp_config_file):
    """Test that get_output_dir returns the correct path."""
    test_config = {
        "random_seed": 42,
        "data_dir": "data",
        "output_dir": "my_outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    output_dir = get_output_dir(config)

    assert output_dir == "my_outputs"

def test_get_log_level(temp_config_file):
    """Test that get_log_level returns the correct level."""
    test_config = {
        "random_seed": 42,
        "data_dir": "data",
        "output_dir": "outputs",
        "log_level": "ERROR",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    log_level = get_log_level(config)

    assert log_level == "ERROR"

def test_get_simulation_config(temp_config_file):
    """Test that get_simulation_config returns the correct config."""
    test_config = {
        "random_seed": 42,
        "data_dir": "data",
        "output_dir": "outputs",
        "simulation": {
            "num_replications": 2000,
            "sample_sizes": [5, 15, 25],
            "confidence_levels": [0.90, 0.95, 0.99],
            "bootstrap_resamples": 2000
        }
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)
    sim_config = get_simulation_config(config)

    assert sim_config["num_replications"] == 2000
    assert sim_config["sample_sizes"] == [5, 15, 25]
    assert sim_config["confidence_levels"] == [0.90, 0.95, 0.99]

def test_deterministic_seed_across_modules(temp_config_file):
    """Test that the seed management works consistently across multiple calls."""
    test_config = {
        "random_seed": 12345,
        "data_dir": "data",
        "output_dir": "outputs",
        "simulation": DEFAULT_CONFIG["simulation"].copy()
    }

    with open(temp_config_file, 'w') as f:
        json.dump(test_config, f)

    config = load_config(temp_config_file)

    # First run
    initialize_random_state(config)
    run1 = [random.random() for _ in range(5)]
    run1_np = np.random.random(5).tolist()

    # Second run with same seed
    initialize_random_state(config)
    run2 = [random.random() for _ in range(5)]
    run2_np = np.random.random(5).tolist()

    # Third run with same seed
    initialize_random_state(config)
    run3 = [random.random() for _ in range(5)]
    run3_np = np.random.random(5).tolist()

    # All runs should be identical
    assert run1 == run2 == run3
    assert run1_np == run2_np == run3_np