"""
Unit tests for utility helpers in code/utils.py.
"""
import pytest
import logging
from pathlib import Path
import sys
import os

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import (
    setup_logging,
    get_project_root,
    get_data_dir,
    get_code_dir,
    get_tests_dir,
    ensure_dir,
    ProjectError,
    DataNotFoundError,
    ConfigurationError,
    APIError
)


class TestSetupLogging:
    def test_setup_logging_default_level(self):
        """Test that setup_logging works with default INFO level."""
        logger = setup_logging()
        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logging_string_level(self):
        """Test that setup_logging handles string levels like 'DEBUG'."""
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_setup_logging_main_fallback(self):
        """Test that setup_logging handles '__main__' string gracefully."""
        logger = setup_logging(level="__main__")
        # Should fallback to INFO without raising ValueError
        assert logger.level == logging.INFO

    def test_setup_logging_duplicate_call(self):
        """Test that calling setup_logging multiple times doesn't duplicate handlers."""
        logger1 = setup_logging(name="test_unique")
        initial_count = len(logger1.handlers)
        
        logger2 = setup_logging(name="test_unique")
        assert len(logger2.handlers) == initial_count


class TestPathResolution:
    def test_get_project_root_exists(self):
        """Test that get_project_root returns a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_dir(self):
        """Test get_data_dir returns correct path structure."""
        data_dir = get_data_dir()
        assert "data" in str(data_dir)
        
        sub_dir = get_data_dir("raw")
        assert "data/raw" in str(sub_dir)

    def test_get_code_dir(self):
        """Test get_code_dir returns correct path structure."""
        code_dir = get_code_dir()
        assert "code" in str(code_dir)

    def test_get_tests_dir(self):
        """Test get_tests_dir returns correct path structure."""
        tests_dir = get_tests_dir()
        assert "tests" in str(tests_dir)

    def test_ensure_dir_creates_new(self, tmp_path):
        """Test that ensure_dir creates a directory if it doesn't exist."""
        new_dir = tmp_path / "new_subdir" / "deep"
        result = ensure_dir(new_dir)
        assert result.exists()
        assert result.is_dir()

    def test_ensure_dir_existing(self, tmp_path):
        """Test that ensure_dir works on existing directory."""
        existing = tmp_path / "existing"
        existing.mkdir()
        result = ensure_dir(existing)
        assert result.exists()


class TestCustomExceptions:
    def test_project_error(self):
        """Test ProjectError can be raised and caught."""
        with pytest.raises(ProjectError):
            raise ProjectError("Test error")

    def test_data_not_found_error(self):
        """Test DataNotFoundError inherits from ProjectError."""
        with pytest.raises(DataNotFoundError):
            raise DataNotFoundError("Data missing")

    def test_configuration_error(self):
        """Test ConfigurationError inherits from ProjectError."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Config invalid")

    def test_api_error(self):
        """Test APIError inherits from ProjectError."""
        with pytest.raises(APIError):
            raise APIError("API call failed")
