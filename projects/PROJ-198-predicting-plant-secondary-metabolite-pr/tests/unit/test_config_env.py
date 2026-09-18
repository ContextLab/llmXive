import os
import pytest
from pathlib import Path
import tempfile
from code.config_env import EnvConfig, load_environment, ensure_directories, get_api_key, get_data_path, validate_required_env_vars

def test_env_config_loading():
    """Test that environment configuration loads correctly."""
    config = load_environment()
    assert isinstance(config, EnvConfig)
    assert config.DATA_ROOT == Path("data")
    assert config.LOGS_DIR == Path("logs")
    assert config.FIGURES_DIR == Path("figures")

def test_ensure_directories():
    """Test that ensure_directories creates required folders."""
    config = load_environment()
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Temporarily override paths
        original_data_root = config.DATA_ROOT
        config.DATA_ROOT = Path(tmp_dir) / "data"
        
        ensure_directories(config)
        
        # Check that directories were created
        assert (Path(tmp_dir) / "data").exists()
        assert (Path(tmp_dir) / "data" / "raw").exists()
        assert (Path(tmp_dir) / "data" / "processed").exists()
        assert (Path(tmp_dir) / "data" / "interim").exists()

def test_get_api_key():
    """Test API key retrieval."""
    config = load_environment()
    
    # Test with no key set
    assert get_api_key("NCBI", config) is None
    
    # Test with key set (if available in environment)
    if config.NCBI_API_KEY:
        assert get_api_key("NCBI", config) == config.NCBI_API_KEY

def test_get_data_path():
    """Test data path construction."""
    config = load_environment()
    
    # Test base path
    assert get_data_path(config) == config.DATA_ROOT
    
    # Test with sub-path
    sub_path = get_data_path(config, "raw/species.fasta")
    assert sub_path == config.DATA_ROOT / "raw" / "species.fasta"

def test_validate_required_env_vars():
    """Test validation of required environment variables."""
    config = load_environment()
    
    # Test with no required services
    assert validate_required_env_vars(config, set()) is True
    
    # Test with required services (will fail if keys not set)
    # This test documents the expected behavior
    result = validate_required_env_vars(config, {"NCBI"})
    # Result depends on whether NCBI_API_KEY is set in environment
    # We just verify the function runs without error
    assert isinstance(result, bool)

def test_env_config_with_custom_paths():
    """Test environment config with custom paths."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Set environment variables before loading
        os.environ["DATA_ROOT"] = str(Path(tmp_dir) / "custom_data")
        os.environ["LOGS_DIR"] = str(Path(tmp_dir) / "custom_logs")
        
        # Reload config (note: in real usage, this would be a new process)
        # For testing, we create a new instance
        config = EnvConfig()
        
        assert config.DATA_ROOT == Path(tmp_dir) / "custom_data"
        assert config.LOGS_DIR == Path(tmp_dir) / "custom_logs"
        
        # Clean up
        del os.environ["DATA_ROOT"]
        del os.environ["LOGS_DIR"]