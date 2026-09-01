import os
import pytest
from pathlib import Path
import tempfile
import shutil

from code.utils.config import (
    _get_project_root,
    _load_env_file,
    init_environment,
    validate_environment,
    get_materials_project_api_key,
    get_materials_project_base_url,
    get_data_path,
    get_raw_data_path,
    get_processed_data_path,
    get_results_path,
    get_custom_dataset_path,
    ensure_data_directories,
    DEFAULT_BASE_URL,
)


class TestConfig:
    """Test cases for config module."""

    def test_get_project_root(self):
        """Test that project root is correctly identified."""
        root = _get_project_root()
        assert root.exists()
        # Should be the parent of code/ directory
        assert (root / "code").exists()

    def test_load_env_file_creates_dict(self):
        """Test that _load_env_file correctly parses env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "TEST_KEY=test_value\n"
                "TEST_KEY_2=another value\n"
                "# This is a comment\n"
                "\n"
                "QUOTED_KEY=\"quoted value\"\n"
                "SINGLE_QUOTED='single quoted'\n"
            )

            _load_env_file(env_path)

            assert os.environ.get("TEST_KEY") == "test_value"
            assert os.environ.get("TEST_KEY_2") == "another value"
            assert os.environ.get("QUOTED_KEY") == "quoted value"
            assert os.environ.get("SINGLE_QUOTED") == "single quoted"

    def test_load_env_file_nonexistent(self):
        """Test that _load_env_file handles missing file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "nonexistent.env"
            # Should not raise
            _load_env_file(env_path)

    def test_validate_environment_missing_key(self, monkeypatch):
        """Test validation fails when required key is missing."""
        # Ensure the key is not set
        monkeypatch.delenv("MATERIALS_PROJECT_API_KEY", raising=False)

        assert validate_environment() is False

    def test_validate_environment_with_key(self, monkeypatch):
        """Test validation passes when required key is set."""
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", "test_key")

        assert validate_environment() is True

    def test_get_materials_project_api_key_missing(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("MATERIALS_PROJECT_API_KEY", raising=False)

        with pytest.raises(ValueError, match="MATERIALS_PROJECT_API_KEY not set"):
            get_materials_project_api_key()

    def test_get_materials_project_api_key_present(self, monkeypatch):
        """Test that API key is returned when set."""
        test_key = "test_api_key_123"
        monkeypatch.setenv("MATERIALS_PROJECT_API_KEY", test_key)

        assert get_materials_project_api_key() == test_key

    def test_get_materials_project_base_url_default(self, monkeypatch):
        """Test default base URL is returned when not set."""
        monkeypatch.delenv("MATERIALS_PROJECT_BASE_URL", raising=False)

        assert get_materials_project_base_url() == DEFAULT_BASE_URL

    def test_get_materials_project_base_url_custom(self, monkeypatch):
        """Test custom base URL is returned when set."""
        custom_url = "https://custom.materialsproject.org"
        monkeypatch.setenv("MATERIALS_PROJECT_BASE_URL", custom_url)

        assert get_materials_project_base_url() == custom_url

    def test_get_data_path_default(self, monkeypatch):
        """Test default data path when DATA_PATH not set."""
        monkeypatch.delenv("DATA_PATH", raising=False)

        path = get_data_path()
        assert path.name == "data"

    def test_get_data_path_custom(self, monkeypatch):
        """Test custom data path when DATA_PATH is set."""
        monkeypatch.setenv("DATA_PATH", "custom_data")

        path = get_data_path()
        assert path.name == "custom_data"

    def test_get_raw_data_path_default(self, monkeypatch):
        """Test default raw data path."""
        monkeypatch.delenv("DATA_RAW_PATH", raising=False)

        path = get_raw_data_path()
        assert path.name == "raw"

    def test_get_processed_data_path_default(self, monkeypatch):
        """Test default processed data path."""
        monkeypatch.delenv("DATA_PROCESSED_PATH", raising=False)

        path = get_processed_data_path()
        assert path.name == "processed"

    def test_get_results_path_default(self, monkeypatch):
        """Test default results path."""
        monkeypatch.delenv("DATA_RESULTS_PATH", raising=False)

        path = get_results_path()
        assert path.name == "results"

    def test_get_custom_dataset_path_none(self, monkeypatch):
        """Test get_custom_dataset_path returns None when not set."""
        monkeypatch.delenv("DATA_CUSTOM_PATH", raising=False)

        assert get_custom_dataset_path() is None

    def test_get_custom_dataset_path_custom(self, monkeypatch):
        """Test get_custom_dataset_path returns path when set."""
        monkeypatch.setenv("DATA_CUSTOM_PATH", "custom/dataset")

        path = get_custom_dataset_path()
        assert path is not None
        assert path.name == "dataset"

    def test_ensure_data_directories_creates(self, monkeypatch, tmp_path):
        """Test that ensure_data_directories creates directories."""
        # Mock _get_project_root to return tmp_path
        import code.utils.config as config_module

        original_get_root = config_module._get_project_root

        def mock_get_root():
            return tmp_path

        config_module._get_project_root = mock_get_root

        try:
            ensure_data_directories()

            assert (tmp_path / "data").exists()
            assert (tmp_path / "data" / "raw").exists()
            assert (tmp_path / "data" / "processed").exists()
            assert (tmp_path / "data" / "results").exists()
        finally:
            config_module._get_project_root = original_get_root

    def test_init_environment_loads_env_file(self, monkeypatch, tmp_path):
        """Test that init_environment loads .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_INIT_KEY=init_value\n")

        # Mock _get_project_root and env path
        import code.utils.config as config_module

        original_get_root = config_module._get_project_root
        original_load_env = config_module._load_env_file

        def mock_get_root():
            return tmp_path

        def mock_load_env(env_path):
            if env_path.exists():
                original_load_env(env_path)

        config_module._get_project_root = mock_get_root
        config_module._load_env_file = mock_load_env

        try:
            init_environment(str(env_file))

            assert os.environ.get("TEST_INIT_KEY") == "init_value"
        finally:
            config_module._get_project_root = original_get_root
            config_module._load_env_file = original_load_env