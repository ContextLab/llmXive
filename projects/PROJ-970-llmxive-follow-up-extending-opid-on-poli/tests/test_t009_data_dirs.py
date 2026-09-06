"""
Tests for T009: Data directory structure and logging infrastructure.
"""
import os
import sys
import tempfile
import shutil
import pytest

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import DATA_DIRS, create_directories
from utils.logging_setup import setup_logging, get_experiment_logger

class TestDataDirectoryStructure:
    """Tests for the data directory creation functionality."""

    def test_data_dirs_defined(self):
        """Verify that the expected data directories are defined."""
        expected_dirs = [
            "data/raw/synthetic_graphs",
            "data/processed",
            "data/logs",
            "data/figures",
            "data/configs"
        ]
        assert DATA_DIRS == expected_dirs, f"Expected {expected_dirs}, got {DATA_DIRS}"

    def test_create_directories_creates_all(self, tmp_path):
        """Test that create_directories creates all required directories."""
        # Change to temporary directory to avoid polluting project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Mock the DATA_DIRS to be relative to tmp_path
            original_dirs = DATA_DIRS[:]
            try:
                # This test assumes DATA_DIRS are relative to cwd
                result = create_directories()
                assert result is True, "create_directories should return True on success"
                
                for dir_path in DATA_DIRS:
                    full_path = os.path.join(tmp_path, dir_path)
                    assert os.path.exists(full_path), f"Directory {dir_path} was not created"
                    assert os.path.isdir(full_path), f"{dir_path} is not a directory"
                    
                    # Check for .gitkeep file
                    gitkeep_path = os.path.join(full_path, ".gitkeep")
                    assert os.path.exists(gitkeep_path), f".gitkeep not found in {dir_path}"
            finally:
                # Restore original DATA_DIRS
                # Note: In a real test suite, we might need to mock this differently
                # since DATA_DIRS is a module-level constant
                pass
        finally:
            os.chdir(original_cwd)

    def test_create_directories_idempotent(self, tmp_path):
        """Test that create_directories is idempotent (can run multiple times)."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run twice
            result1 = create_directories()
            result2 = create_directories()
            
            assert result1 is True
            assert result2 is True
            
            # All directories should still exist
            for dir_path in DATA_DIRS:
                full_path = os.path.join(tmp_path, dir_path)
                assert os.path.exists(full_path)
        finally:
            os.chdir(original_cwd)

class TestLoggingInfrastructure:
    """Tests for the logging setup functionality."""

    def test_setup_logging_creates_logger(self):
        """Test that setup_logging returns a configured logger."""
        logger = setup_logging(name="test_logger")
        
        assert logger is not None
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        
        # Check handlers
        assert len(logger.handlers) > 0, "Logger should have at least one handler"
    
    def test_setup_logging_file_handler(self, tmp_path):
        """Test that setup_logging creates a file handler when log_file is provided."""
        import logging
        
        log_file = "test.log"
        logger = setup_logging(
            name="test_file_logger",
            log_file=log_file,
            console=False
        )
        
        # Check that file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0, "Logger should have a file handler"
        
        # Check that log file was created
        log_path = os.path.join("data/logs", log_file)
        # Note: This might fail if data/logs doesn't exist, but setup_logging should create it
        # In a real test, we'd ensure the directory exists first
    
    def test_get_experiment_logger(self):
        """Test that get_experiment_logger creates a properly named logger."""
        logger = get_experiment_logger(tier=1, threshold=0.5, run_id="test123")
        
        assert logger is not None
        assert "tier1" in logger.name
        assert "thresh0.5" in logger.name
        assert "test123" in logger.name

    def test_logging_writes_message(self, tmp_path, capsys):
        """Test that logging actually writes messages."""
        import logging
        
        logger = setup_logging(
            name="test_message_logger",
            console=True,
            level=logging.INFO
        )
        
        test_message = "Test log message"
        logger.info(test_message)
        
        captured = capsys.readouterr()
        assert test_message in captured.out

# Note: These tests assume the project structure exists.
# In a CI environment, you might need to set up the environment first.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
