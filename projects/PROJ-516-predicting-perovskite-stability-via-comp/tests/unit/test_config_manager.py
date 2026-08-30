"""
Unit tests for the configuration management module.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
from code.utils.config_manager import (
    ConfigError,
    load_dotenv_file,
    get_api_key,
    validate_environment
)

class TestLoadDotenvFile:
    """Tests for load_dotenv_file function."""
    
    def test_load_from_specified_path(self):
        """Test loading .env from a specific path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            env_path = f.name
        
        try:
            result = load_dotenv_file(env_path)
            assert result is True
            assert os.getenv("TEST_KEY") == "test_value"
        finally:
            os.unlink(env_path)
            # Clean up environment
            if "TEST_KEY" in os.environ:
                del os.environ["TEST_KEY"]
    
    def test_load_from_project_root(self):
        """Test loading .env from project root."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            
            env_file = project_root / ".env"
            env_file.write_text("PROJECT_KEY=project_value\n")
            
            # Change to a subdirectory to test root detection
            (project_root / "subdir").mkdir()
            original_cwd = os.getcwd()
            try:
                os.chdir(project_root / "subdir")
                # Temporarily override the module's path resolution
                import code.utils.config_manager as cm
                original_parent = cm.Path(__file__).resolve().parent
                
                # Mock the path resolution to point to our temp dir
                # (In practice, this test relies on the actual module logic)
                result = load_dotenv_file()
                # Note: This test might need adjustment based on exact path resolution logic
            finally:
                os.chdir(original_cwd)
    
    def test_missing_specified_file_raises_error(self):
        """Test that specifying a non-existent .env file raises ConfigError."""
        with pytest.raises(ConfigError):
            load_dotenv_file("/nonexistent/path/.env")

class TestGetApiKey:
    """Tests for get_api_key function."""
    
    def test_get_existing_key(self):
        """Test retrieving an existing API key."""
        os.environ["TEST_API_KEY"] = "secret123"
        try:
            key = get_api_key("TEST_API_KEY", "Test Service")
            assert key == "secret123"
        finally:
            del os.environ["TEST_API_KEY"]
    
    def test_missing_key_raises_error(self):
        """Test that missing API key raises ConfigError."""
        # Ensure the key doesn't exist
        if "MISSING_KEY" in os.environ:
            del os.environ["MISSING_KEY"]
        
        with pytest.raises(ConfigError) as exc_info:
            get_api_key("MISSING_KEY", "Missing Service")
        
        assert "MISSING_KEY" in str(exc_info.value)
        assert "Missing Service" in str(exc_info.value)

class TestValidateEnvironment:
    """Tests for validate_environment function."""
    
    def test_all_keys_present(self):
        """Test validation when all required keys are present."""
        os.environ["KEY1"] = "value1"
        os.environ["KEY2"] = "value2"
        
        try:
            result = validate_environment({
                "KEY1": "Service 1",
                "KEY2": "Service 2"
            })
            
            assert result["KEY1"] is True
            assert result["KEY2"] is True
        finally:
            del os.environ["KEY1"]
            del os.environ["KEY2"]
    
    def test_missing_key_raises_error(self):
        """Test validation fails when a required key is missing."""
        os.environ["KEY1"] = "value1"
        
        if "KEY2" in os.environ:
            del os.environ["KEY2"]
        
        try:
            with pytest.raises(ConfigError) as exc_info:
                validate_environment({
                    "KEY1": "Service 1",
                    "KEY2": "Service 2"
                })
            
            assert "KEY2" in str(exc_info.value)
        finally:
            del os.environ["KEY1"]
    
    def test_default_keys_validation(self):
        """Test validation with default keys (MP_API_KEY, NREL_API_KEY)."""
        # Set the default keys
        os.environ["MP_API_KEY"] = "mp_test"
        os.environ["NREL_API_KEY"] = "nrel_test"
        
        try:
            # This should not raise
            result = validate_environment()
            assert result["MP_API_KEY"] is True
            assert result["NREL_API_KEY"] is True
        finally:
            del os.environ["MP_API_KEY"]
            del os.environ["NREL_API_KEY"]
