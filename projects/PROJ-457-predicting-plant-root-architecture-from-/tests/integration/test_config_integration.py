"""
Integration tests for configuration and logging.
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    load_config,
    get_config,
    get_seed,
    get_data_path,
    setup_logging,
    get_logger,
    PROJECT_ROOT
)


def test_full_config_workflow():
    """Test the complete configuration workflow."""
    # Load config
    config = load_config()
    
    # Verify all expected keys exist
    expected_keys = [
        "DATA_PATH", "SEED", "LOG_LEVEL", 
        "FIGURES_PATH", "REPORTS_PATH", "MODELS_PATH",
        "LOG_FILE", "OUTPUT_PATH"
    ]
    
    for key in expected_keys:
        assert key in config, f"Missing key: {key}"
    
    # Verify paths are valid
    data_path = get_data_path()
    assert data_path.exists() or data_path.parent.exists()
    
    # Verify seed is valid
    seed = get_seed()
    assert isinstance(seed, int)
    assert seed >= 0
    
    # Verify logging works
    logger = setup_logging()
    logger.info("Configuration integration test passed")
    
    # Verify log file exists
    log_file = get_config("LOG_FILE")
    assert Path(log_file).exists()


def test_config_with_nonexistent_file():
    """Test behavior when config file doesn't exist."""
    import config
    
    # Temporarily point to non-existent file
    original_path = config.CONFIG_PATH
    config.CONFIG_PATH = Path("/nonexistent/config.yaml")
    config._config = None  # Reset cache
    
    try:
        # Should fall back to defaults without crashing
        loaded_config = load_config()
        assert isinstance(loaded_config, dict)
        assert "SEED" in loaded_config
    finally:
        # Restore original path
        config.CONFIG_PATH = original_path
        config._config = None
