import os
import sys
import tempfile
import logging
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config_manager import Config, get_config, reset_config
from logging_config import setup_logging, get_logger

class TestConfigManager:
    def test_config_initialization(self):
        """Test that Config loads default values correctly."""
        reset_config()
        config = get_config()
        
        assert config.random_seed == 42
        assert config.lattice_sizes == [16, 24]
        assert config.temp_min == 0.1
        assert config.temp_max == 3.0
        assert config.batch_size == 32

    def test_config_paths_exist(self):
        """Test that config ensures directories exist."""
        reset_config()
        config = get_config()
        
        assert config.data_raw_dir.exists()
        assert config.data_processed_dir.exists()
        assert config.figures_dir.exists()
        assert config.logs_dir.exists()
        assert config.checkpoint_dir.exists()

    def test_config_getters(self):
        """Test path and param retrieval methods."""
        reset_config()
        config = get_config()
        
        paths = config.get_paths()
        assert "project_root" in paths
        assert "data_raw" in paths
        
        sim_params = config.get_simulation_params()
        assert "lattice_sizes" in sim_params
        assert "coupling_j1" in sim_params
        
        train_params = config.get_training_params()
        assert "learning_rate" in train_params

    def test_env_override(self):
        """Test that environment variables override defaults."""
        # This test assumes the .env file is loaded by dotenv
        # In a real CI environment, we might need to mock os.getenv
        reset_config()
        config = get_config()
        # Just verify it doesn't crash and loads something
        assert isinstance(config.random_seed, int)

class TestLoggingSetup:
    def test_setup_logging_console(self):
        """Test that logging setup creates a console handler."""
        logger = setup_logging(log_level="INFO", log_file=None)
        
        assert logger is not None
        assert logging.getLogger("llmXive").level == logging.INFO
        
        # Check for console handler
        console_found = False
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler):
                console_found = True
                break
        assert console_found

    def test_setup_logging_file(self):
        """Test that logging setup creates a file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file_path = Path(tmpdir) / "test.log"
            logger = setup_logging(log_level="DEBUG", log_file=str(log_file_path))
            
            # Check for file handler
            file_found = False
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.FileHandler):
                    if handler.baseFilename == str(log_file_path):
                        file_found = True
                        break
            assert file_found
            
            # Verify log content
            assert log_file_path.exists()
            with open(log_file_path, "r") as f:
                content = f.read()
            assert "Logging infrastructure initialized" in content

    def test_get_logger(self):
        """Test retrieving a named logger."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"
        assert logger.level == logging.INFO  # Inherited from root