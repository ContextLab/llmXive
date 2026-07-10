"""
Unit tests for utils.py functions.
"""
import os
import random
import tempfile
import logging
from pathlib import Path
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import (
    setup_logging,
    get_logger,
    calculate_checksum,
    pin_random_seed,
    validate_tools_and_log,
    validate_tools_and_log_wrapper
)


class TestSetupLogging:
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging returns a logger instance."""
        logger = setup_logging(log_level=logging.DEBUG, log_to_file=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive_research"
        
    def test_setup_logging_sets_level(self):
        """Test that setup_logging sets the correct log level."""
        logger = setup_logging(log_level=logging.WARNING, log_to_file=False)
        assert logger.level == logging.WARNING
        
    def test_get_logger_returns_child(self):
        """Test that get_logger can create child loggers."""
        setup_logging(log_to_file=False)
        child_logger = get_logger("test_child")
        assert child_logger.name == "llmXive_research.test_child"


class TestCalculateChecksum:
    def test_calculate_checksum_sha256(self):
        """Test SHA256 checksum calculation."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = calculate_checksum(temp_path, "sha256")
            assert len(checksum) == 64  # SHA256 hex length
            assert all(c in "0123456789abcdef" for c in checksum)
        finally:
            os.unlink(temp_path)
            
    def test_calculate_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum(Path("nonexistent_file.txt"))
            
    def test_calculate_checksum_invalid_algorithm(self):
        """Test that ValueError is raised for invalid algorithm."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                calculate_checksum(temp_path, "invalid_algo")
        finally:
            os.unlink(temp_path)


class TestPinRandomSeed:
    def test_pin_random_seed_affects_python_random(self):
        """Test that pin_random_seed affects Python's random module."""
        pin_random_seed(42)
        val1 = random.random()
        
        pin_random_seed(42)
        val2 = random.random()
        
        assert val1 == val2
        
    def test_pin_random_seed_affects_numpy(self):
        """Test that pin_random_seed affects numpy if available."""
        try:
            import numpy as np
            pin_random_seed(123)
            val1 = np.random.rand()
            
            pin_random_seed(123)
            val2 = np.random.rand()
            
            assert val1 == val2
        except ImportError:
            pytest.skip("numpy not installed")


class TestValidateTools:
    def test_validate_tools_returns_list(self):
        """Test that validate_tools_and_log returns a list."""
        results = validate_tools_and_log(["radon", "semgrep"])
        assert isinstance(results, list)
        assert len(results) == 2
        
    def test_validate_tools_structure(self):
        """Test that each tool result has expected keys."""
        results = validate_tools_and_log(["radon"])
        assert len(results) == 1
        tool_info = results[0]
        assert "name" in tool_info
        assert "version" in tool_info
        assert "stars" in tool_info
        assert "citation_match" in tool_info
        assert "valid" in tool_info
        
    def test_validate_tools_log_file_created(self):
        """Test that validation creates log file."""
        from utils import LOG_DIR
        log_file = LOG_DIR / "tool_validation_log.csv"
        
        # Remove file if exists
        if log_file.exists():
            log_file.unlink()
        
        validate_tools_and_log(["radon"])
        assert log_file.exists()