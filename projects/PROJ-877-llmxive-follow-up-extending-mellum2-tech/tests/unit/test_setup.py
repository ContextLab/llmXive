"""
Unit tests for setup and logging functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest

from setup_logging import setup_logger, log_directory_creation
from setup_directories import ensure_data_directories, generate_init_files

class TestSetupLogging:
    """Tests for setup_logging module."""
    
    def test_setup_logger_creates_logger(self):
        """Test that setup_logger returns a configured logger."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0
        
    def test_setup_logger_with_file(self):
        """Test that setup_logger can write to a file."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp:
            log_path = tmp.name
            
        try:
            logger = setup_logger("test_file_logger", log_file=log_path)
            logger.info("Test message")
            
            # Check that file was created and contains message
            assert os.path.exists(log_path)
            with open(log_path, 'r') as f:
                content = f.read()
            assert "Test message" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)
                
    def test_log_directory_creation(self, caplog):
        """Test that log_directory_creation logs the correct message."""
        with caplog.at_level(logging.INFO):
            log_directory_creation("test_type", "/test/path", "test_caplog")
            
        assert any("TEST TYPE CREATED: /test/path" in record.message 
                  for record in caplog.records)

class TestSetupDirectories:
    """Tests for setup_directories module."""
    
    def test_ensure_data_directories_creates_structure(self, tmp_path):
        """Test that ensure_data_directories creates required structure."""
        # Temporarily override get_project_root
        import setup_directories
        original_get_project_root = setup_directories.get_project_root
        
        setup_directories.get_project_root = lambda: tmp_path
        
        try:
            created_dirs = ensure_data_directories()
            
            # Check that root was created
            assert tmp_path.exists()
            
            # Check that subdirectories were created
            required_subdirs = ["code", "data", "tests", "data/raw", 
                              "data/processed", "data/results"]
            
            for subdir in required_subdirs:
                assert (tmp_path / subdir).exists()
                
            # Check return value
            assert len(created_dirs) > 0
            for path_str, created_flag in created_dirs:
                assert Path(path_str).exists()
        finally:
            setup_directories.get_project_root = original_get_project_root
            
    def test_generate_init_files(self, tmp_path):
        """Test that generate_init_files creates __init__.py files."""
        import setup_directories
        original_get_project_root = setup_directories.get_project_root
        
        setup_directories.get_project_root = lambda: tmp_path
        
        try:
            # Create some package directories
            (tmp_path / "code").mkdir()
            (tmp_path / "tests").mkdir()
            
            init_files = generate_init_files()
            
            # Check that init files were created
            assert len(init_files) > 0
            
            for init_file in init_files:
                assert os.path.exists(init_file)
                with open(init_file, 'r') as f:
                    content = f.read()
                assert "Package initialization" in content
        finally:
            setup_directories.get_project_root = original_get_project_root