import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from env_manager import (
    load_env_vars,
    get_env_var,
    get_data_path,
    validate_data_paths,
    setup_environment,
    DEFAULT_DATA_ROOT,
    DEFAULT_RAW_DATA_DIR,
    DEFAULT_PROCESSED_DATA_DIR,
    DEFAULT_FIGURES_DIR
)


class TestLoadEnvVars:
    def test_load_from_existing_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n")
        
        result = load_env_vars(env_file)
        
        assert result == {"KEY1": "value1", "KEY2": "value2"}
        assert os.getenv("KEY1") == "value1"
        assert os.getenv("KEY2") == "value2"
    
    def test_load_ignores_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nKEY=value\n")
        
        result = load_env_vars(env_file)
        
        assert result == {"KEY": "value"}
    
    def test_load_ignores_empty_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nKEY=value\n\n")
        
        result = load_env_vars(env_file)
        
        assert result == {"KEY": "value"}
    
    def test_load_nonexistent_file_returns_empty(self, tmp_path):
        result = load_env_vars(tmp_path / "nonexistent.env")
        assert result == {}


class TestGetEnvVar:
    def test_get_existing_var(self):
        os.environ["TEST_KEY"] = "test_value"
        assert get_env_var("TEST_KEY") == "test_value"
    
    def test_get_nonexistent_var_with_default(self):
        assert get_env_var("NONEXISTENT_KEY", "default") == "default"
    
    def test_get_nonexistent_var_without_default(self):
        assert get_env_var("NONEXISTENT_KEY") is None


class TestGetDataPath:
    def test_default_data_root(self):
        # Ensure no custom env var is set
        if "LXXIVE_DATA_ROOT" in os.environ:
            del os.environ["LXXIVE_DATA_ROOT"]
        
        path = get_data_path()
        expected = Path.cwd() / DEFAULT_DATA_ROOT
        assert path == expected
    
    def test_with_sub_path(self):
        if "LXXIVE_DATA_ROOT" in os.environ:
            del os.environ["LXXIVE_DATA_ROOT"]
        
        path = get_data_path("raw")
        expected = Path.cwd() / DEFAULT_DATA_ROOT / "raw"
        assert path == expected
    
    def test_with_custom_env_root(self, tmp_path):
        custom_root = tmp_path / "custom_data"
        with patch.dict(os.environ, {"LXXIVE_DATA_ROOT": str(custom_root)}):
            path = get_data_path()
            assert path == custom_root
    
    def test_creates_directory_when_requested(self, tmp_path):
        test_dir = tmp_path / "test_create"
        with patch.dict(os.environ, {"LXXIVE_DATA_ROOT": str(tmp_path)}):
            path = get_data_path("test_create", create=True)
            assert path.exists()
            assert path.is_dir()


class TestValidateDataPaths:
    def test_validates_and_creates_missing_dirs(self, tmp_path):
        # Patch to use tmp_path as root
        with patch.dict(os.environ, {"LXXIVE_DATA_ROOT": str(tmp_path)}):
            # Remove env vars that might be set from previous tests
            for key in ["LXXIVE_RAW_DATA_DIR", "LXXIVE_PROCESSED_DATA_DIR", "LXXIVE_FIGURES_DIR"]:
                if key in os.environ:
                    del os.environ[key]
            
            result = validate_data_paths()
            assert result is True
            
            # Verify directories were created
            assert (tmp_path / DEFAULT_RAW_DATA_DIR).exists()
            assert (tmp_path / DEFAULT_PROCESSED_DATA_DIR).exists()
            assert (tmp_path / DEFAULT_FIGURES_DIR).exists()


class TestSetupEnvironment:
    def test_setup_creates_all_directories(self, tmp_path):
        with patch.dict(os.environ, {"LXXIVE_DATA_ROOT": str(tmp_path)}):
            # Clear specific overrides to test defaults
            for key in ["LXXIVE_RAW_DATA_DIR", "LXXIVE_PROCESSED_DATA_DIR", "LXXIVE_FIGURES_DIR"]:
                if key in os.environ:
                    del os.environ[key]
            
            paths = setup_environment()
            
            assert 'data_root' in paths
            assert 'raw' in paths
            assert 'processed' in paths
            assert 'figures' in paths
            
            assert paths['raw'].exists()
            assert paths['processed'].exists()
            assert paths['figures'].exists()
            
            assert paths['raw'] == tmp_path / DEFAULT_RAW_DATA_DIR
            assert paths['processed'] == tmp_path / DEFAULT_PROCESSED_DATA_DIR
            assert paths['figures'] == tmp_path / DEFAULT_FIGURES_DIR
