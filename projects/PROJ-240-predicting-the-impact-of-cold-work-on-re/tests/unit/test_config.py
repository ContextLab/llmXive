"""
Unit tests for configuration management (T009).

Tests verify that:
1. Environment variables are loaded correctly
2. .env file is parsed properly
3. Default values are used when environment variables are not set
4. Type conversion works correctly for all configuration values
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the config module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    load_env_config,
    get_config_value,
    get_n_permutations,
    get_random_seed,
    get_data_split_ratio,
    get_min_rows,
    get_max_rows,
    get_outlier_percentile,
    get_project_root,
    DEFAULT_N_PERMUTATIONS,
    DEFAULT_RANDOM_SEED,
    DEFAULT_DATA_SPLIT_RATIO,
    DEFAULT_MIN_ROWS,
    DEFAULT_MAX_ROWS,
    DEFAULT_OUTLIER_PERCENTILE,
    ENV_N_PERMUTATIONS,
    ENV_RANDOM_SEED,
    ENV_DATA_SPLIT_RATIO,
    ENV_MIN_ROWS,
    ENV_MAX_ROWS,
    ENV_OUTLIER_PERCENTILE
)

@pytest.fixture
def clean_env():
    """Clean up environment variables before and after each test."""
    # Save original values
    original = {}
    for key in [ENV_N_PERMUTATIONS, ENV_RANDOM_SEED, ENV_DATA_SPLIT_RATIO, 
                ENV_MIN_ROWS, ENV_MAX_ROWS, ENV_OUTLIER_PERCENTILE]:
        if key in os.environ:
            original[key] = os.environ[key]
            del os.environ[key]
    
    yield original
    
    # Restore original values
    for key, value in original.items():
        os.environ[key] = value

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(f"{ENV_N_PERMUTATIONS}=500\n")
        f.write(f"{ENV_RANDOM_SEED}=123\n")
        f.write(f"{ENV_DATA_SPLIT_RATIO}=0.3\n")
        f.write(f"{ENV_MIN_ROWS}=100\n")
        f.write(f"{ENV_MAX_ROWS}=5000\n")
        f.write(f"{ENV_OUTLIER_PERCENTILE}=95\n")
        f.write("# This is a comment\n")
        f.write("\n")
        f.write(f'{ENV_N_PERMUTATIONS}="800"\n')  # Test quoted values
        env_path = f.name
    
    yield env_path
    
    # Clean up
    os.unlink(env_path)

def test_load_env_config_defaults(clean_env):
    """Test that default values are used when no environment variables are set."""
    config = load_env_config()
    
    assert config[ENV_N_PERMUTATIONS] == DEFAULT_N_PERMUTATIONS
    assert config[ENV_RANDOM_SEED] == DEFAULT_RANDOM_SEED
    assert config[ENV_DATA_SPLIT_RATIO] == DEFAULT_DATA_SPLIT_RATIO
    assert config[ENV_MIN_ROWS] == DEFAULT_MIN_ROWS
    assert config[ENV_MAX_ROWS] == DEFAULT_MAX_ROWS
    assert config[ENV_OUTLIER_PERCENTILE] == DEFAULT_OUTLIER_PERCENTILE

def test_load_env_config_from_environment(clean_env):
    """Test that environment variables are loaded correctly."""
    os.environ[ENV_N_PERMUTATIONS] = "750"
    os.environ[ENV_RANDOM_SEED] = "999"
    os.environ[ENV_DATA_SPLIT_RATIO] = "0.15"
    os.environ[ENV_MIN_ROWS] = "25"
    os.environ[ENV_MAX_ROWS] = "20000"
    os.environ[ENV_OUTLIER_PERCENTILE] = "90"
    
    config = load_env_config()
    
    assert config[ENV_N_PERMUTATIONS] == 750
    assert config[ENV_RANDOM_SEED] == 999
    assert config[ENV_DATA_SPLIT_RATIO] == 0.15
    assert config[ENV_MIN_ROWS] == 25
    assert config[ENV_MAX_ROWS] == 20000
    assert config[ENV_OUTLIER_PERCENTILE] == 90

def test_load_env_config_from_file(temp_env_file, clean_env):
    """Test that .env file is loaded correctly."""
    config = load_env_config(Path(temp_env_file))
    
    # Values from .env file should be loaded
    assert config[ENV_N_PERMUTATIONS] == 500  # First value, not the quoted one
    assert config[ENV_RANDOM_SEED] == 123
    assert config[ENV_DATA_SPLIT_RATIO] == 0.3
    assert config[ENV_MIN_ROWS] == 100
    assert config[ENV_MAX_ROWS] == 5000
    assert config[ENV_OUTLIER_PERCENTILE] == 95

def test_get_config_value(clean_env):
    """Test get_config_value function."""
    config = load_env_config()
    
    # Test getting existing value
    assert get_config_value(config, ENV_N_PERMUTATIONS) == DEFAULT_N_PERMUTATIONS
    
    # Test getting non-existing value with default
    assert get_config_value(config, "NON_EXISTENT", "default") == "default"
    
    # Test getting non-existing value without default
    assert get_config_value(config, "NON_EXISTENT") is None

def test_get_n_permutations(clean_env):
    """Test get_n_permutations helper function."""
    assert get_n_permutations() == DEFAULT_N_PERMUTATIONS
    
    os.environ[ENV_N_PERMUTATIONS] = "2000"
    assert get_n_permutations() == 2000

def test_get_random_seed(clean_env):
    """Test get_random_seed helper function."""
    assert get_random_seed() == DEFAULT_RANDOM_SEED
    
    os.environ[ENV_RANDOM_SEED] = "12345"
    assert get_random_seed() == 12345

def test_get_data_split_ratio(clean_env):
    """Test get_data_split_ratio helper function."""
    assert get_data_split_ratio() == DEFAULT_DATA_SPLIT_RATIO
    
    os.environ[ENV_DATA_SPLIT_RATIO] = "0.25"
    assert get_data_split_ratio() == 0.25

def test_get_min_rows(clean_env):
    """Test get_min_rows helper function."""
    assert get_min_rows() == DEFAULT_MIN_ROWS
    
    os.environ[ENV_MIN_ROWS] = "75"
    assert get_min_rows() == 75

def test_get_max_rows(clean_env):
    """Test get_max_rows helper function."""
    assert get_max_rows() == DEFAULT_MAX_ROWS
    
    os.environ[ENV_MAX_ROWS] = "15000"
    assert get_max_rows() == 15000

def test_get_outlier_percentile(clean_env):
    """Test get_outlier_percentile helper function."""
    assert get_outlier_percentile() == DEFAULT_OUTLIER_PERCENTILE
    
    os.environ[ENV_OUTLIER_PERCENTILE] = "97"
    assert get_outlier_percentile() == 97

def test_invalid_values_fallback(clean_env):
    """Test that invalid values fall back to defaults."""
    os.environ[ENV_N_PERMUTATIONS] = "invalid"
    os.environ[ENV_DATA_SPLIT_RATIO] = "not_a_number"
    
    config = load_env_config()
    
    assert config[ENV_N_PERMUTATIONS] == DEFAULT_N_PERMUTATIONS
    assert config[ENV_DATA_SPLIT_RATIO] == DEFAULT_DATA_SPLIT_RATIO

def test_n_permutations_for_statistical_tests(clean_env):
    """Test that N_PERMUTATIONS is set to 1000 as required by T009."""
    # Explicitly set to 1000
    os.environ[ENV_N_PERMUTATIONS] = "1000"
    
    config = load_env_config()
    assert config[ENV_N_PERMUTATIONS] == 1000
    assert get_n_permutations(config) == 1000
    
    # Verify it's the default
    del os.environ[ENV_N_PERMUTATIONS]
    config = load_env_config()
    assert config[ENV_N_PERMUTATIONS] == DEFAULT_N_PERMUTATIONS
    assert DEFAULT_N_PERMUTATIONS == 1000