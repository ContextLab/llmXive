"""
Tests for environment variable management (T008).

This module tests the EnvConfig class to ensure proper handling of
environment variables for data paths and seeds.
"""
import os
import tempfile
import pytest
from pathlib import Path
from utils.env_config import EnvConfig, EnvConfigError, get_config, reset_config

@pytest.fixture
def clean_env():
    """Fixture to clean environment variables before each test."""
    # Store original values
    original = {}
    keys = ["DATA_ROOT", "RANDOM_SEED", "LOG_LEVEL", "QUERY_LOG_PATH", 
            "SYNTHETIC_DATA_PATH", "MERGED_DATASET_PATH", "MODEL_METRICS_PATH",
            "MODEL_ARTIFACT_PATH", "INTERPRETATION_REPORT_PATH",
            "FEATURE_IMPORTANCE_PVALUES_PATH", "SHAP_PLOT_PATH",
            "VALIDATION_REPORT_PATH", "STABILITY_METRICS_PATH",
            "OVERLAP_REPORT_PATH", "PERF_METRICS_PATH"]
    
    for key in keys:
        if key in os.environ:
            original[key] = os.environ[key]
            del os.environ[key]
    
    # Reset config singleton
    reset_config()
    
    yield
    
    # Restore original values
    for key, value in original.items():
        os.environ[key] = value
    reset_config()

def test_default_configuration(clean_env):
    """Test that default configuration values are set correctly."""
    config = get_config()
    
    assert config.data_root == Path("./data")
    assert config.raw_data_dir == Path("./data/raw")
    assert config.processed_data_dir == Path("./data/processed")
    assert config.results_dir == Path("./data/results")
    assert config.models_dir == Path("./data/models")
    assert config.seed == 42
    assert config.log_level == "INFO"

def test_custom_data_root(clean_env):
    """Test custom DATA_ROOT environment variable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["DATA_ROOT"] = tmpdir
        reset_config()
        config = get_config()
        
        assert config.data_root == Path(tmpdir)
        assert config.raw_data_dir == Path(tmpdir) / "raw"
        assert config.processed_data_dir == Path(tmpdir) / "processed"
        assert config.results_dir == Path(tmpdir) / "results"
        assert config.models_dir == Path(tmpdir) / "models"

def test_custom_seed(clean_env):
    """Test custom RANDOM_SEED environment variable."""
    os.environ["RANDOM_SEED"] = "12345"
    reset_config()
    config = get_config()
    
    assert config.seed == 12345

def test_invalid_seed_raises_error(clean_env):
    """Test that non-integer RANDOM_SEED raises EnvConfigError."""
    os.environ["RANDOM_SEED"] = "not_a_number"
    reset_config()
    
    with pytest.raises(EnvConfigError, match="RANDOM_SEED must be an integer"):
        get_config()

def test_custom_log_level(clean_env):
    """Test custom LOG_LEVEL environment variable."""
    os.environ["LOG_LEVEL"] = "DEBUG"
    reset_config()
    config = get_config()
    
    assert config.log_level == "DEBUG"

def test_custom_file_paths(clean_env):
    """Test custom file path environment variables."""
    os.environ["QUERY_LOG_PATH"] = "/custom/query_log.json"
    os.environ["MERGED_DATASET_PATH"] = "/custom/merged.csv"
    os.environ["MODEL_METRICS_PATH"] = "/custom/metrics.json"
    
    reset_config()
    config = get_config()
    
    assert config.query_log_path == Path("/custom/query_log.json")
    assert config.merged_dataset_path == Path("/custom/merged.csv")
    assert config.model_metrics_path == Path("/custom/metrics.json")

def test_to_dict(clean_env):
    """Test that to_dict returns a valid dictionary."""
    config = get_config()
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert "data_root" in config_dict
    assert "seed" in config_dict
    assert config_dict["seed"] == 42

def test_to_json(clean_env):
    """Test that to_json returns a valid JSON string."""
    import json
    config = get_config()
    json_str = config.to_json()
    
    # Should not raise an exception
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert "data_root" in parsed

def test_validate_creates_directories(clean_env):
    """Test that validate() creates missing directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["DATA_ROOT"] = tmpdir
        reset_config()
        config = get_config()
        
        # Directories should not exist yet
        assert not config.raw_data_dir.exists()
        assert not config.processed_data_dir.exists()
        
        # Validate should create them
        config.validate()
        
        assert config.raw_data_dir.exists()
        assert config.processed_data_dir.exists()
        assert config.results_dir.exists()
        assert config.models_dir.exists()

def test_validate_non_writable_directory(clean_env):
    """Test that validate() raises error for non-writable directory."""
    # This test is skipped on Windows as permission handling differs
    if os.name == "nt":
        pytest.skip("Permission handling differs on Windows")
        
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ["DATA_ROOT"] = tmpdir
        reset_config()
        config = get_config()
        
        # Create a directory and make it read-only
        config.raw_data_dir.mkdir(parents=True, exist_ok=True)
        config.raw_data_dir.chmod(0o444)
        
        try:
            with pytest.raises(EnvConfigError, match="not writable"):
                config.validate()
        finally:
            # Restore permissions for cleanup
            config.raw_data_dir.chmod(0o755)

def test_singleton_pattern(clean_env):
    """Test that get_config returns the same instance."""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2

def test_reset_config(clean_env):
    """Test that reset_config() clears the singleton."""
    config1 = get_config()
    reset_config()
    config2 = get_config()
    
    assert config1 is not config2
