import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import ensure_data_directories, generate_init_files, main
from config import get_project_root

class TestSetupDirectories:
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock configuration with a temporary project root."""
        return {
            "project_root": str(tmp_path)
        }

    @pytest.fixture
    def mock_get_project_root(self, tmp_path):
        """Mock get_project_root to return a temporary directory."""
        with patch('setup_directories.get_project_root', return_value=tmp_path):
            with patch('config.get_project_root', return_value=tmp_path):
                yield tmp_path

    def test_ensure_data_directories_creates_new_dirs(self, mock_get_project_root):
        """Test that ensure_data_directories creates the required subdirectories."""
        tmp_path = mock_get_project_root
        config = {"project_root": str(tmp_path)}
        
        # Verify directories don't exist initially
        assert not (tmp_path / "code").exists()
        assert not (tmp_path / "data").exists()
        
        # Run the function
        created_dirs = ensure_data_directories(config)
        
        # Verify directories were created
        assert len(created_dirs) > 0
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "tests").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "data" / "results").exists()

    def test_ensure_data_directories_skips_existing_dirs(self, mock_get_project_root):
        """Test that ensure_data_directories doesn't recreate existing directories."""
        tmp_path = mock_get_project_root
        config = {"project_root": str(tmp_path)}
        
        # Create some directories beforehand
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        
        # Run the function
        created_dirs = ensure_data_directories(config)
        
        # Verify only missing directories were reported as created
        # (code and data should not be in created_dirs)
        assert not any("code" in d for d in created_dirs)
        assert not any("data" in d for d in created_dirs)

    def test_generate_init_files_creates_init_files(self, mock_get_project_root):
        """Test that generate_init_files creates __init__.py files."""
        tmp_path = mock_get_project_root
        config = {"project_root": str(tmp_path)}
        
        # Create required directories first
        ensure_data_directories(config)
        (tmp_path / "code" / "analysis").mkdir(parents=True)
        (tmp_path / "code" / "data").mkdir(parents=True)
        
        # Run the function
        created_files = generate_init_files(config)
        
        # Verify __init__.py files were created
        assert len(created_files) > 0
        assert (tmp_path / "code" / "__init__.py").exists()
        assert (tmp_path / "code" / "analysis" / "__init__.py").exists()
        assert (tmp_path / "code" / "data" / "__init__.py").exists()

    def test_generate_init_files_skips_existing_init_files(self, mock_get_project_root):
        """Test that generate_init_files doesn't recreate existing __init__.py files."""
        tmp_path = mock_get_project_root
        config = {"project_root": str(tmp_path)}
        
        # Create directories and init files beforehand
        ensure_data_directories(config)
        (tmp_path / "code").mkdir(exist_ok=True)
        (tmp_path / "code" / "__init__.py").touch()
        
        # Run the function
        created_files = generate_init_files(config)
        
        # Verify __init__.py was not reported as created
        assert not any("__init__.py" in f for f in created_files)

    def test_main_creates_log_file(self, mock_get_project_root, caplog):
        """Test that main function creates the log file."""
        tmp_path = mock_get_project_root
        
        # Run main
        with patch('setup_directories.get_config', return_value={"project_root": str(tmp_path)}):
            main()
        
        # Verify log file was created
        log_file = tmp_path / "data" / "results" / "project_subdirs_creation.log"
        assert log_file.exists()
        
        # Verify log file contains expected content
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Project Subdirectory Creation Log" in content
            assert "Directories Created:" in content
            assert "code" in content
            assert "data" in content