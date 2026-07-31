import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from code.utils.config import get_project_root, get_results_dir
from code.utils.directories import create_results_directories, create_all_directories

@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    return logger

def test_create_results_directories(mock_logger):
    """Test that create_results_directories creates the required structure."""
    # We can't easily test the actual file system creation in a unit test
    # without side effects, so we mock the path operations.
    with patch('code.utils.directories.get_results_dir') as mock_get_dir:
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_dir = Path("/fake/results")
            mock_get_dir.return_value = mock_dir

            create_results_directories(mock_logger)

            # Verify mkdir was called 3 times (results, reports, plots)
            assert mock_mkdir.call_count == 3
            
            # Verify logger was called for each directory
            assert mock_logger.info.call_count == 3

def test_create_all_directories(mock_logger):
    """Test that create_all_directories creates all required structures."""
    with patch('code.utils.directories.get_project_root') as mock_proj_root:
        with patch('code.utils.directories.get_data_dir') as mock_data_dir:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                mock_proj = Path("/fake/project")
                mock_data = Path("/fake/data")
                mock_proj_root.return_value = mock_proj
                mock_data_dir.return_value = mock_data

                create_all_directories(mock_logger)

                # Verify mkdir was called for all directories
                # code (5), data (5), tests (4), results (3) = 17 calls
                # Note: The actual count depends on implementation details
                # We just verify it's called multiple times
                assert mock_mkdir.call_count > 10
                
                # Verify logger was called for each directory
                assert mock_logger.info.call_count > 10

def test_directory_paths_exist():
    """Test that the directory paths returned by config functions are valid Path objects."""
    proj_root = get_project_root()
    results_dir = get_results_dir()
    
    assert isinstance(proj_root, Path)
    assert isinstance(results_dir, Path)
    assert results_dir.name == "results"
    assert str(results_dir).startswith(str(proj_root))
