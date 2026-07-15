"""
Tests for the Python environment setup script.
"""
import sys
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

# Import the module under test
# We need to add the code directory to the path to import it
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_python_env import check_python_version, get_requirements_path

class TestCheckPythonVersion:
    def test_valid_python_3_10(self):
        """Test that Python 3.10 passes."""
        with patch('setup_python_env.sys') as mock_sys:
            mock_sys.version_info.major = 3
            mock_sys.version_info.minor = 10
            # Should not raise
            check_python_version()

    def test_valid_python_3_11(self):
        """Test that Python 3.11 passes (future proofing)."""
        with patch('setup_python_env.sys') as mock_sys:
            mock_sys.version_info.major = 3
            mock_sys.version_info.minor = 11
            # Should not raise
            check_python_version()

    def test_invalid_python_3_9(self):
        """Test that Python 3.9 raises an error."""
        with patch('setup_python_env.sys') as mock_sys:
            mock_sys.version_info.major = 3
            mock_sys.version_info.minor = 9
            with pytest.raises(RuntimeError) as excinfo:
                check_python_version()
            assert "too low" in str(excinfo.value)

    def test_invalid_python_2_7(self):
        """Test that Python 2.7 raises an error."""
        with patch('setup_python_env.sys') as mock_sys:
            mock_sys.version_info.major = 2
            mock_sys.version_info.minor = 7
            with pytest.raises(RuntimeError) as excinfo:
                check_python_version()
            assert "version mismatch" in str(excinfo.value)

class TestGetRequirementsPath:
    def test_finds_requirements_in_parent(self, tmp_path):
        """Test that the function finds requirements.txt in the parent directory."""
        # Create a fake requirements.txt in tmp_path
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("torch\n")
        
        # Create a subdirectory to simulate code/
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        # Mock the __file__ attribute of the module
        with patch('setup_python_env.Path') as mock_path:
            # Mock the return value of resolve() to point to our temp code dir
            mock_path.return_value.resolve.return_value.parent = tmp_path
            
            # We need to patch the specific call inside the function
            # Since get_requirements_path uses Path(__file__) internally,
            # we patch the module-level Path
            import setup_python_env as env_module
            original_path = env_module.Path
            
            def mock_path_constructor(path=None):
                if path is None:
                    # This is called as Path(__file__)
                    mock_obj = MagicMock()
                    mock_obj.resolve.return_value.parent = tmp_path
                    return mock_obj
                return original_path(path)
            
            env_module.Path = mock_path_constructor
            
            try:
                result = env_module.get_requirements_path()
                assert result == req_file
            finally:
                env_module.Path = original_path

    def test_raises_when_missing(self, tmp_path):
        """Test that FileNotFoundError is raised if requirements.txt is missing."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        
        import setup_python_env as env_module
        original_path = env_module.Path
        
        def mock_path_constructor(path=None):
            if path is None:
                mock_obj = MagicMock()
                mock_obj.resolve.return_value.parent = tmp_path
                return mock_obj
            return original_path(path)
        
        env_module.Path = mock_path_constructor
        
        try:
            with pytest.raises(FileNotFoundError):
                env_module.get_requirements_path()
        finally:
            env_module.Path = original_path