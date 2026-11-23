"""
Tests for configuration management (T008).

Verifies that environment variables are loaded correctly,
paths are validated, and random seeds are set properly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the config module (adjust import path based on project structure)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.config import ProjectConfig, ConfigError, get_config, reset_config

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("DATA_RAW_PATH=/tmp/test_raw\n")
        f.write("DATA_PROCESSED_PATH=/tmp/test_processed\n")
        f.write("DATA_RESULTS_PATH=/tmp/test_results\n")
        f.write("DATA_MODELS_PATH=/tmp/test_models\n")
        f.write("RANDOM_SEED=123\n")
        f.write("LOG_LEVEL=DEBUG\n")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def cleanup_dirs():
    """Clean up test directories after test."""
    yield
    # Cleanup handled by pytest temp dirs or manual cleanup if needed

def test_config_loads_from_env_file(temp_env_file):
    """Test that configuration loads correctly from .env file."""
    config = ProjectConfig(env_path=temp_env_file)
    
    assert config.data_raw_path == Path("/tmp/test_raw")
    assert config.data_processed_path == Path("/tmp/test_processed")
    assert config.data_results_path == Path("/tmp/test_results")
    assert config.data_models_path == Path("/tmp/test_models")
    assert config.random_seed == 123
    assert config.log_level == "DEBUG"

def test_config_uses_defaults_when_missing():
    """Test that configuration uses defaults when env vars are missing."""
    # Create a minimal env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("# Empty config\n")
        env_path = Path(f.name)
    
    try:
        config = ProjectConfig(env_path=env_path)
        
        # Check that default paths are used (relative to project root)
        project_root = Path(__file__).parent.parent
        assert config.data_raw_path == project_root / "data" / "raw"
        assert config.random_seed == 42
        assert config.log_level == "INFO"
    finally:
        os.unlink(env_path)

def test_config_invalid_seed_raises_error():
    """Test that invalid random seed raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("RANDOM_SEED=not_a_number\n")
        env_path = Path(f.name)
    
    try:
        with pytest.raises(ConfigError):
            ProjectConfig(env_path=env_path)
    finally:
        os.unlink(env_path)

def test_config_creates_directories(temp_env_file):
    """Test that configuration creates necessary directories."""
    # Use unique temp directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create custom env file with temp paths
        custom_env = tmp_path / "test.env"
        with open(custom_env, 'w') as f:
            f.write(f"DATA_RAW_PATH={tmp_path / 'raw'}\n")
            f.write(f"DATA_PROCESSED_PATH={tmp_path / 'processed'}\n")
            f.write(f"DATA_RESULTS_PATH={tmp_path / 'results'}\n")
            f.write(f"DATA_MODELS_PATH={tmp_path / 'models'}\n")
        
        config = ProjectConfig(env_path=custom_env)
        
        # Verify directories were created
        assert config.data_raw_path.exists()
        assert config.data_processed_path.exists()
        assert config.data_results_path.exists()
        assert config.data_models_path.exists()

def test_get_config_singleton():
    """Test that get_config returns singleton instance."""
    reset_config()
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2
    reset_config()

def test_config_to_dict():
    """Test configuration serialization to dictionary."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("DATA_RAW_PATH=/test/raw\n")
        f.write("DATA_PROCESSED_PATH=/test/processed\n")
        f.write("DATA_RESULTS_PATH=/test/results\n")
        f.write("DATA_MODELS_PATH=/test/models\n")
        f.write("RANDOM_SEED=999\n")
        f.write("LOG_LEVEL=WARNING\n")
        env_path = Path(f.name)
    
    try:
        config = ProjectConfig(env_path=env_path)
        config_dict = config.to_dict()
        
        assert config_dict["data_raw_path"] == "/test/raw"
        assert config_dict["random_seed"] == 999
        assert config_dict["log_level"] == "WARNING"
        assert "data_processed_path" in config_dict
        assert "data_results_path" in config_dict
        assert "data_models_path" in config_dict
    finally:
        os.unlink(env_path)
