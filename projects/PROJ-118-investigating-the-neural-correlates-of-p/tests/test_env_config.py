"""
Unit tests for environment configuration management (T009).
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.env_config import (
    get_project_root,
    get_openneuro_api_key,
    get_path,
    ensure_directory,
    validate_environment,
    DEFAULT_PATHS
)

class TestGetProjectRoot:
    def test_default_to_cwd(self, tmp_path):
        """Test that root defaults to current working directory."""
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                root = get_project_root()
                assert root == tmp_path.resolve()

    def test_uses_project_root_env(self):
        """Test that PROJECT_ROOT env var is respected."""
        mock_root = Path("/fake/project/root")
        with patch('pathlib.Path.cwd', return_value=Path("/fake")):
            with patch.dict(os.environ, {"PROJECT_ROOT": str(mock_root)}):
                root = get_project_root()
                assert root == mock_root.resolve()

    def test_non_existent_root_raises(self):
        """Test that non-existent root raises FileNotFoundError."""
        mock_root = Path("/definitely/does/not/exist")
        with patch('pathlib.Path.cwd', return_value=Path("/fake")):
            with patch.dict(os.environ, {"PROJECT_ROOT": str(mock_root)}):
                with pytest.raises(FileNotFoundError):
                    get_project_root()

class TestGetOpenNeuroApiKey:
    def test_returns_key(self):
        """Test retrieval of API key."""
        test_key = "test_key_123"
        with patch.dict(os.environ, {"OPENNEURO_API_KEY": test_key}):
            key = get_openneuro_api_key()
            assert key == test_key

    def test_missing_key_raises(self):
        """Test that missing key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENNEURO_API_KEY environment variable is not set"):
                get_openneuro_api_key()

class TestGetPath:
    @pytest.fixture
    def mock_root(self, tmp_path):
        return tmp_path

    def test_valid_path_name(self, mock_root):
        """Test resolving a known path name."""
        with patch('code.env_config.get_project_root', return_value=mock_root):
            path = get_path("data_raw")
            expected = mock_root / DEFAULT_PATHS["data_raw"]
            assert path == expected.resolve()

    def test_invalid_path_name(self, mock_root):
        """Test that unknown path name raises KeyError."""
        with patch('code.env_config.get_project_root', return_value=mock_root):
            with pytest.raises(KeyError):
                get_path("non_existent_path")

    def test_relative_to_override(self, mock_root, tmp_path):
        """Test overriding the base path."""
        custom_base = tmp_path / "custom"
        path = get_path("data_raw", relative_to=custom_base)
        expected = custom_base / DEFAULT_PATHS["data_raw"]
        assert path == expected.resolve()

class TestEnsureDirectory:
    def test_creates_directory(self, tmp_path):
        """Test that ensure_directory creates the folder."""
        target = tmp_path / "new_dir"
        result = ensure_directory(path=target)
        assert result == target.resolve()
        assert target.exists()
        assert target.is_dir()

    def test_existing_directory_no_error(self, tmp_path):
        """Test that existing directory passes without error."""
        target = tmp_path / "existing_dir"
        target.mkdir()
        result = ensure_directory(path=target)
        assert result == target.resolve()

    def test_neither_path_nor_name_raises(self):
        """Test that missing arguments raise ValueError."""
        with pytest.raises(ValueError, match="Must provide either 'path' or 'name'"):
            ensure_directory()

class TestValidateEnvironment:
    def test_success(self, tmp_path):
        """Test successful validation."""
        # Setup mock environment
        os.environ["OPENNEURO_API_KEY"] = "valid_key"
        os.environ["PROJECT_ROOT"] = str(tmp_path)
        
        # Ensure required dirs exist for validation
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        (tmp_path / "data" / "processed").mkdir()
        (tmp_path / "results").mkdir()
        (tmp_path / "code").mkdir()
        (tmp_path / "tests").mkdir()

        # Should not raise
        validate_environment()

    def test_missing_api_key_fails(self):
        """Test that missing API key causes validation to fail."""
        os.environ.pop("OPENNEURO_API_KEY", None)
        with pytest.raises(ValueError):
            validate_environment()