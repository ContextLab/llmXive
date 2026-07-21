"""
Unit tests for logger and config utilities.
"""
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.logger import get_logger, setup_logging
from src.utils.config import Config, get_config, DEFAULT_AR_THRESHOLD


class TestLogger:
    def test_setup_logging_creates_file(self, tmp_path):
        """Verify that setup_logging creates the log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_dir=tmp_path, log_file="test.log", console=False)
        
        # Force a log message to ensure file is created and written to
        logger = get_logger("test_logger_setup")
        logger.info("Initialization test")
        
        assert log_file.exists()

    def test_get_logger_returns_valid_instance(self):
        """Verify that get_logger returns a valid Logger instance."""
        # Ensure logging is initialized
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=Path(tmpdir), console=False)
        
        logger = get_logger("test_module")
        assert logger is not None
        assert isinstance(logger, type(get_logger("")))
        assert logger.name == "test_module"

    def test_logger_name_matches_module(self):
        """Verify logger name reflects the requested name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_dir=Path(tmpdir), console=False)
        
        logger = get_logger("specific.module.name")
        assert logger.name == "specific.module.name"


class TestConfig:
    def test_config_defaults(self):
        """Verify default values are set correctly."""
        # Clear singleton to force re-init with defaults
        from src.utils.config import _config_instance
        import src.utils.config as config_module
        config_module._config_instance = None
        
        cfg = get_config()
        assert cfg.ar_threshold == DEFAULT_AR_THRESHOLD
        assert cfg.lat_min == 20.0
        assert cfg.lat_max == 60.0
        assert cfg.start_year == 1979
        assert cfg.end_year == 2023

    def test_config_from_env(self):
        """Verify Config reads from environment variables."""
        # Clear singleton
        import src.utils.config as config_module
        config_module._config_instance = None
        
        # Set env vars
        original_env = os.environ.copy()
        try:
            os.environ["AR_THRESHOLD"] = "100.5"
            os.environ["LAT_MIN"] = "25.0"
            os.environ["DATA_ROOT"] = "/tmp/test_data"
            
            cfg = get_config()
            assert cfg.ar_threshold == 100.5
            assert cfg.lat_min == 25.0
            assert cfg.data_root == Path("/tmp/test_data")
        finally:
            os.environ.clear()
            os.environ.update(original_env)
            # Reset singleton
            config_module._config_instance = None

    def test_config_path_resolution(self, tmp_path):
        """Verify paths are resolved relative to cwd."""
        # Clear singleton
        import src.utils.config as config_module
        config_module._config_instance = None
        
        original_cwd = os.getcwd()
        try:
            # Change to temp dir to test relative resolution
            os.chdir(tmp_path)
            cfg = get_config()
            
            # Check that processed_dir is inside tmp_path
            assert cfg.processed_dir.parent == tmp_path
            assert cfg.processed_dir.name == "processed"
        finally:
            os.chdir(original_cwd)
            config_module._config_instance = None