"""
Tests for the environment variable management module (env_config.py).
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We are testing code/env_config.py, so we import from code.env_config
# However, the task description refers to 'code/env_manager.py' in the API surface.
# Looking at the provided API surface, the file is actually 'code/env_manager.py'
# and the public names are: load_env_vars, get_env_var, get_data_path, etc.
# But the code I just wrote is in 'code/env_config.py'.
# I need to align with the API surface provided in the prompt.
# The prompt says:
# ### code/env_manager.py
# import as: `from env_manager import load_env_vars, ...`
# So I must rename my file to env_manager.py or the tests must import from env_config.
# The prompt's "Existing project API surface" lists `code/env_manager.py`.
# Therefore, I must produce `code/env_manager.py` instead of `code/env_config.py`.
# I will update the artifact path in the final output to match the API surface.
# For now, assuming the file is named env_manager.py as per the API surface.

from code.env_manager import (
    load_env_vars,
    get_env_var,
    get_data_path,
    get_raw_data_path,
    get_processed_data_path,
    get_models_artifacts_path,
    validate_data_paths,
    get_silso_url,
    get_sorce_url,
    setup_environment,
    DOTENV_AVAILABLE
)

class TestLoadEnvVars:
    def test_load_env_vars_no_file(self, tmp_path):
        """Test loading when .env file does not exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = load_env_vars(tmp_path / ".env")
            assert result is True  # Should not fail if file missing

    @pytest.mark.skipif(not DOTENV_AVAILABLE, reason="python-dotenv not installed")
    def test_load_env_vars_success(self, tmp_path):
        """Test loading a valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\n")
        
        # Unset the env var first to ensure we get the loaded one
        if "TEST_VAR" in os.environ:
            del os.environ["TEST_VAR"]
        
        result = load_env_vars(env_file)
        assert result is True
        assert os.getenv("TEST_VAR") == "test_value"

class TestGetEnvVar:
    def test_get_env_var_existing(self):
        """Test getting an existing env var."""
        os.environ["TEST_KEY"] = "test_value"
        assert get_env_var("TEST_KEY") == "test_value"
        del os.environ["TEST_KEY"]

    def test_get_env_var_default(self):
        """Test getting a non-existing env var with default."""
        assert get_env_var("NON_EXISTENT_KEY", default="default_val") == "default_val"

    def test_get_env_var_required_missing(self):
        """Test getting a required env var that is missing."""
        with pytest.raises(ValueError, match="Required environment variable"):
            get_env_var("NON_EXISTENT_KEY", required=True)

class TestGetPaths:
    def test_get_data_path_default(self):
        """Test getting data path with default."""
        # Clear env to test default
        if "DATA_ROOT" in os.environ:
            del os.environ["DATA_ROOT"]
        
        path = get_data_path()
        assert str(path) == "data"

    def test_get_data_path_sub(self):
        """Test getting data path with sub-path."""
        if "DATA_ROOT" in os.environ:
            del os.environ["DATA_ROOT"]
        
        path = get_data_path("raw")
        assert str(path) == "data/raw"

    def test_get_raw_data_path(self):
        """Test getting raw data path."""
        if "DATA_RAW" in os.environ:
            del os.environ["DATA_RAW"]
        path = get_raw_data_path()
        assert str(path) == "data/raw"

    def test_get_processed_data_path(self):
        """Test getting processed data path."""
        if "DATA_PROCESSED" in os.environ:
            del os.environ["DATA_PROCESSED"]
        path = get_processed_data_path()
        assert str(path) == "data/processed"

    def test_get_models_artifacts_path(self):
        """Test getting models artifacts path."""
        if "MODELS_ARTIFACTS" in os.environ:
            del os.environ["MODELS_ARTIFACTS"]
        path = get_models_artifacts_path()
        assert str(path) == "code/models/artifacts"

class TestValidateDataPaths:
    def test_validate_paths(self, tmp_path):
        """Test validation of data paths."""
        # Create the necessary directories
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        models_dir = tmp_path / "code" / "models" / "artifacts"
        
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        
        with patch('code.env_manager.get_raw_data_path', return_value=raw_dir), \
             patch('code.env_manager.get_processed_data_path', return_value=processed_dir), \
             patch('code.env_manager.get_models_artifacts_path', return_value=models_dir):
            
            results = validate_data_paths()
            assert results["raw"] is True
            assert results["processed"] is True
            assert results["models_artifacts"] is True

class TestGetUrls:
    def test_get_silso_url_default(self):
        """Test getting SILSO URL with default."""
        if "SILSO_URL" in os.environ:
            del os.environ["SILSO_URL"]
        url = get_silso_url()
        assert url == "https://www.sidc.be/users/iv/homogene/sunspot/"

    def test_get_sorce_url_default(self):
        """Test getting SORCE URL with default."""
        if "SORCE_URL" in os.environ:
            del os.environ["SORCE_URL"]
        url = get_sorce_url()
        assert url == "https://lasp.colorado.edu/sorce/"

class TestSetupEnvironment:
    def test_setup_environment(self, tmp_path):
        """Test setting up the environment."""
        # Create dummy directories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        (tmp_path / "code" / "models" / "artifacts").mkdir(parents=True)
        
        with patch('code.env_manager.get_raw_data_path', return_value=tmp_path / "data" / "raw"), \
             patch('code.env_manager.get_processed_data_path', return_value=tmp_path / "data" / "processed"), \
             patch('code.env_manager.get_models_artifacts_path', return_value=tmp_path / "code" / "models" / "artifacts"):
            
                # Should not raise
                setup_environment()
