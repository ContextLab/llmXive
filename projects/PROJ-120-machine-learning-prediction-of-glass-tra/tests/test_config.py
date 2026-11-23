"""
Tests for the environment configuration management module.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import (
    load_environment,
    get_zenodo_doi,
    get_zenodo_api_url,
    get_raw_data_dir,
    get_processed_data_dir,
    validate_configuration,
    initialize_config,
    REQUIRED_VARS
)


class TestLoadEnvironment:
    """Tests for the load_environment function."""

    def test_load_from_default_path(self, tmp_path, monkeypatch):
        """Test loading .env from default project root path."""
        # Create a mock .env file
        env_file = tmp_path / ".env"
        env_file.write_text("ZENODO_DOI=10.1234/test\nZENODO_API_URL=https://zenodo.org/api\n")
        
        # Mock get_project_root to return tmp_path
        with patch("config.get_project_root", return_value=tmp_path):
            result = load_environment()
            assert result is True
            assert os.getenv("ZENODO_DOI") == "10.1234/test"

    def test_load_from_custom_path(self, tmp_path):
        """Test loading .env from a custom path."""
        custom_env = tmp_path / "custom.env"
        custom_env.write_text("ZENODO_DOI=10.5678/custom\n")
        
        result = load_environment(custom_env)
        assert result is True
        assert os.getenv("ZENODO_DOI") == "10.5678/custom"

    def test_missing_env_file_returns_false(self, tmp_path, monkeypatch):
        """Test that missing .env file returns False."""
        with patch("config.get_project_root", return_value=tmp_path):
            result = load_environment()
            assert result is False


class TestGetZenodoDoi:
    """Tests for get_zenodo_doi function."""

    def test_valid_doi(self, monkeypatch):
        """Test retrieving a valid DOI."""
        monkeypatch.setenv("ZENODO_DOI", "10.1234/valid_doi")
        doi = get_zenodo_doi()
        assert doi == "10.1234/valid_doi"

    def test_missing_doi_raises_error(self, monkeypatch):
        """Test that missing DOI raises RuntimeError."""
        monkeypatch.delenv("ZENODO_DOI", raising=False)
        with pytest.raises(RuntimeError, match="ZENODO_DOI environment variable is not set"):
            get_zenodo_doi()


class TestGetZenodoApiUrl:
    """Tests for get_zenodo_api_url function."""

    def test_custom_url(self, monkeypatch):
        """Test retrieving a custom API URL."""
        monkeypatch.setenv("ZENODO_API_URL", "https://custom.zenodo.org/api")
        url = get_zenodo_api_url()
        assert url == "https://custom.zenodo.org/api"

    def test_default_url(self, monkeypatch):
        """Test retrieving the default API URL when not set."""
        monkeypatch.delenv("ZENODO_API_URL", raising=False)
        url = get_zenodo_api_url()
        assert url == "https://zenodo.org/api"

    def test_empty_url_raises_error(self, monkeypatch):
        """Test that empty URL raises RuntimeError."""
        monkeypatch.setenv("ZENODO_API_URL", "")
        with pytest.raises(RuntimeError, match="ZENODO_API_URL environment variable is empty"):
            get_zenodo_api_url()


class TestGetRawDataDir:
    """Tests for get_raw_data_dir function."""

    def test_valid_path(self, monkeypatch):
        """Test retrieving a valid data directory path."""
        monkeypatch.setenv("RAW_DATA_DIR", "/tmp/raw_data")
        path = get_raw_data_dir()
        assert isinstance(path, Path)
        assert str(path) == "/tmp/raw_data"

    def test_missing_path_raises_error(self, monkeypatch):
        """Test that missing path raises RuntimeError."""
        monkeypatch.delenv("RAW_DATA_DIR", raising=False)
        with pytest.raises(RuntimeError, match="RAW_DATA_DIR environment variable is not set"):
            get_raw_data_dir()


class TestGetProcessedDataDir:
    """Tests for get_processed_data_dir function."""

    def test_valid_path(self, monkeypatch):
        """Test retrieving a valid processed data directory path."""
        monkeypatch.setenv("PROCESSED_DATA_DIR", "/tmp/processed_data")
        path = get_processed_data_dir()
        assert isinstance(path, Path)
        assert str(path) == "/tmp/processed_data"

    def test_missing_path_raises_error(self, monkeypatch):
        """Test that missing path raises RuntimeError."""
        monkeypatch.delenv("PROCESSED_DATA_DIR", raising=False)
        with pytest.raises(RuntimeError, match="PROCESSED_DATA_DIR environment variable is not set"):
            get_processed_data_dir()


class TestValidateConfiguration:
    """Tests for validate_configuration function."""

    def test_all_vars_present(self, monkeypatch):
        """Test validation passes when all variables are present."""
        for var in REQUIRED_VARS:
            monkeypatch.setenv(var, f"value_for_{var}")
        
        assert validate_configuration() is True

    def test_missing_var_raises_error(self, monkeypatch):
        """Test validation fails when a variable is missing."""
        for var in REQUIRED_VARS:
            if var != "ZENODO_DOI":
                monkeypatch.setenv(var, "value")
        
        # ZENODO_DOI is not set
        with pytest.raises(RuntimeError, match="Missing required environment variables"):
            validate_configuration()


class TestInitializeConfig:
    """Tests for initialize_config function."""

    def test_full_initialization(self, tmp_path, monkeypatch):
        """Test full configuration initialization."""
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            "ZENODO_DOI=10.1234/test\n"
            "ZENODO_API_URL=https://zenodo.org/api\n"
            "RAW_DATA_DIR=/tmp/raw\n"
            "PROCESSED_DATA_DIR=/tmp/processed\n"
        )

        with patch("config.get_project_root", return_value=tmp_path):
            config = initialize_config()
            
            assert config["doi"] == "10.1234/test"
            assert config["api_url"] == "https://zenodo.org/api"
            assert config["raw_data_dir"] == "/tmp/raw"
            assert config["processed_data_dir"] == "/tmp/processed"

    def test_initialization_failure(self, tmp_path, monkeypatch):
        """Test initialization fails when required vars are missing."""
        env_file = tmp_path / ".env"
        env_file.write_text("ZENODO_DOI=10.1234/test\n")  # Missing others

        with patch("config.get_project_root", return_value=tmp_path):
            with pytest.raises(RuntimeError):
                initialize_config()