"""Unit tests for the configuration loader."""

import os
import tempfile
from pathlib import Path

import pytest

# Import the module under test
# We use a relative import style that works when tests are run from the project root
import sys
from pathlib import Path

# Add the code directory to the path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.config import (
    get_project_root, 
    get_data_dir, 
    get_results_dir, 
    load_env_config
)
from utils.logging import setup_logging, get_logger


class TestProjectRoot:
    """Tests for project root detection."""

    def test_project_root_exists(self):
        """Test that project root is detected correctly."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # Should contain tasks.md
        assert (root / "tasks.md").exists()

    def test_project_root_is_absolute(self):
        """Test that project root is an absolute path."""
        root = get_project_root()
        assert root.is_absolute()


class TestDirectoryPaths:
    """Tests for directory path helpers."""

    def test_data_dir_is_path(self):
        """Test that data_dir returns a Path object."""
        data_dir = get_data_dir()
        assert isinstance(data_dir, Path)

    def test_results_dir_is_path(self):
        """Test that results_dir returns a Path object."""
        results_dir = get_results_dir()
        assert isinstance(results_dir, Path)

    def test_data_dir_exists_or_parent_exists(self):
        """Test that data directory or its parent exists."""
        data_dir = get_data_dir()
        # The path should be valid (parent should exist)
        assert data_dir.parent.exists()

    def test_results_dir_exists_or_parent_exists(self):
        """Test that results directory or its parent exists."""
        results_dir = get_results_dir()
        assert results_dir.parent.exists()


class TestLoadEnvConfig:
    """Tests for environment configuration loading."""

    def test_load_config_returns_dict(self):
        """Test that load_env_config returns a dictionary."""
        config = load_env_config()
        assert isinstance(config, dict)

    def test_config_contains_project_root(self):
        """Test that config contains project_root key."""
        config = load_env_config()
        assert "project_root" in config

    def test_config_contains_data_dir(self):
        """Test that config contains data_dir key."""
        config = load_env_config()
        assert "data_dir" in config

    def test_config_contains_seed(self):
        """Test that config contains seed key."""
        config = load_env_config()
        assert "seed" in config
        assert isinstance(config["seed"], int)

    def test_config_with_yaml_file(self):
        """Test loading config from a YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("seed: 12345\nlog_level: DEBUG\n")
            yaml_path = f.name
        
        try:
            config = load_env_config(yaml_path)
            assert config["seed"] == 12345
            assert config["log_level"] == "DEBUG"
        finally:
            os.unlink(yaml_path)

    def test_config_env_override(self):
        """Test that environment variables override defaults."""
        original_seed = os.getenv("SEED")
        try:
            os.environ["SEED"] = "99999"
            config = load_env_config()
            assert config["seed"] == 99999
        finally:
            if original_seed is not None:
                os.environ["SEED"] = original_seed
            elif "SEED" in os.environ:
                del os.environ["SEED"]

class TestLogging:
    """Tests for logging setup."""

    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a logger."""
        logger = setup_logging()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger."""
        logger = get_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_name(self):
        """Test that get_logger with name returns a child logger."""
        logger = get_logger("test_module")
        assert logger.name == "llmXive.test_module"

    def test_logging_to_file(self):
        """Test logging to a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
            log_path = f.name
        
        try:
            logger = setup_logging(log_file=log_path)
            logger.info("Test message")
            
            # Check file was created and contains message
            assert Path(log_path).exists()
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test message" in content
        finally:
            if Path(log_path).exists():
                os.unlink(log_path)

import logging