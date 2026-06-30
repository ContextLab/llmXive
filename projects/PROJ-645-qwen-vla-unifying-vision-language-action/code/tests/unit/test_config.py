"""
Unit tests for the environment configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

# Import the module under test
# Adjust import path based on project structure (code/src/utils/config)
from src.utils.config import Config

class TestConfig:
    """Test cases for Config class."""

    def test_default_data_dir(self):
        """Test that default data directory is set correctly."""
        # Ensure no env var is set to force default
        with patch.dict(os.environ, {}, clear=False):
            if "DATA_DIR" in os.environ:
                del os.environ["DATA_DIR"]
            
            data_dir = Config.get_data_dir()
            assert isinstance(data_dir, Path)
            assert data_dir.name == "data"

    def test_default_checkpoints_dir_creation(self):
        """Test that checkpoints directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Set a temporary path that doesn't exist yet
            temp_checkpoints = Path(tmp_dir) / "nonexistent" / "checkpoints"
            
            with patch.dict(os.environ, {"CHECKPOINTS_DIR": str(temp_checkpoints)}):
                result_path = Config.get_checkpoints_dir()
                assert result_path.exists()
                assert result_path == temp_checkpoints

    def test_wall_time_limit_default(self):
        """Test default wall time limit is 6 hours (21600s)."""
        with patch.dict(os.environ, {}, clear=False):
            if "WALL_TIME_LIMIT_SECONDS" in os.environ:
                del os.environ["WALL_TIME_LIMIT_SECONDS"]
            
            limit = Config.get_wall_time_limit_seconds()
            assert limit == 21600

    def test_ram_limit_default(self):
        """Test default RAM limit is 7.0 GB."""
        with patch.dict(os.environ, {}, clear=False):
            if "RAM_LIMIT_GB" in os.environ:
                del os.environ["RAM_LIMIT_GB"]
            
            limit = Config.get_ram_limit_gb()
            assert limit == 7.0

    def test_num_threads_default(self):
        """Test default number of threads is 2."""
        with patch.dict(os.environ, {}, clear=False):
            if "NUM_THREADS" in os.environ:
                del os.environ["NUM_THREADS"]
            
            threads = Config.get_num_threads()
            assert threads == 2

    def test_custom_batch_size(self):
        """Test custom batch size from environment variable."""
        with patch.dict(os.environ, {"BATCH_SIZE": "32"}):
            batch_size = Config.get_batch_size()
            assert batch_size == 32

    def test_get_dataset_path(self):
        """Test dataset path construction."""
        with patch.dict(os.environ, {"DATA_DIR": "/tmp/test_data"}):
            path = Config.get_dataset_path("open_x_embodiment")
            assert str(path) == "/tmp/test_data/open_x_embodiment.parquet"

    def test_to_dict(self):
        """Test configuration export to dictionary."""
        config_dict = Config.to_dict()
        
        assert "paths" in config_dict
        assert "hyperparameters" in config_dict
        assert "runtime" in config_dict
        
        assert "data_dir" in config_dict["paths"]
        assert "batch_size" in config_dict["hyperparameters"]
        assert "model_name" in config_dict["runtime"]

    def test_log_level_default(self):
        """Test default log level is INFO."""
        import logging
        with patch.dict(os.environ, {}, clear=False):
            if "LOG_LEVEL" in os.environ:
                del os.environ["LOG_LEVEL"]
            
            level = Config.get_log_level()
            assert level == logging.INFO

    def test_log_level_custom(self):
        """Test custom log level from environment variable."""
        import logging
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = Config.get_log_level()
            assert level == logging.DEBUG

    def test_model_name_default(self):
        """Test default model name."""
        with patch.dict(os.environ, {}, clear=False):
            if "MODEL_NAME" in os.environ:
                del os.environ["MODEL_NAME"]
            
            name = Config.get_model_name()
            assert name == "Qwen2-VL-2B"

    def test_experiment_seed_default(self):
        """Test default experiment seed."""
        with patch.dict(os.environ, {}, clear=False):
            if "EXPERIMENT_SEED" in os.environ:
                del os.environ["EXPERIMENT_SEED"]
            
            seed = Config.get_experiment_seed()
            assert seed == 42
