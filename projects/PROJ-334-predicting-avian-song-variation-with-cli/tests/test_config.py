import os
import pytest
from pathlib import Path
import tempfile
import shutil
from code.config import Config


class TestConfig:
    """Tests for the base configuration loader."""

    def test_default_initialization(self):
        """Test that Config initializes with default paths."""
        config = Config()
        assert config.root is not None
        assert config.data_dir is not None
        assert config.data_raw is not None
        assert config.data_processed is not None
        assert config.contracts_dir is not None
        assert config.figures_dir is not None
        assert config.models_dir is not None
        assert config.checksums_file is not None

    def test_paths_are_absolute(self):
        """Test that all paths are absolute."""
        config = Config()
        assert config.root.is_absolute()
        assert config.data_dir.is_absolute()
        assert config.data_raw.is_absolute()
        assert config.data_processed.is_absolute()
        assert config.contracts_dir.is_absolute()
        assert config.figures_dir.is_absolute()
        assert config.models_dir.is_absolute()

    def test_directories_exist(self):
        """Test that required directories are created."""
        config = Config()
        assert config.data_raw.exists()
        assert config.data_processed.exists()
        assert config.figures_dir.exists()
        assert config.models_dir.exists()

    def test_custom_env_root(self):
        """Test that Config respects AVIAN_SONG_ROOT environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["AVIAN_SONG_ROOT"] = tmpdir
            try:
                config = Config()
                assert Path(tmpdir) == config.root
            finally:
                del os.environ["AVIAN_SONG_ROOT"]

    def test_custom_env_data_dir(self):
        """Test that Config respects AVIAN_SONG_DATA_DIR environment variable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["AVIAN_SONG_DATA_DIR"] = tmpdir
            try:
                config = Config()
                assert Path(tmpdir) == config.data_dir
            finally:
                del os.environ["AVIAN_SONG_DATA_DIR"]

    def test_get_path_relative_to_root(self):
        """Test get_path returns correct path relative to root."""
        config = Config()
        test_path = "some/nested/file.txt"
        result = config.get_path(test_path)
        expected = config.root / test_path
        assert result == expected
        assert result.is_absolute()

    def test_get_data_path_relative_to_data(self):
        """Test get_data_path returns correct path relative to data dir."""
        config = Config()
        test_path = "raw/sample.csv"
        result = config.get_data_path(test_path)
        expected = config.data_dir / test_path
        assert result == expected
        assert result.is_absolute()

    def test_to_dict(self):
        """Test that to_dict returns a valid dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "root" in config_dict
        assert "data_dir" in config_dict
        assert "data_raw" in config_dict
        assert "data_processed" in config_dict
        assert "contracts_dir" in config_dict
        assert "figures_dir" in config_dict
        assert "models_dir" in config_dict
        assert "checksums_file" in config_dict

    def test_checksums_file_location(self):
        """Test that checksums_file is in the data directory."""
        config = Config()
        assert config.checksums_file.parent == config.data_dir
        assert config.checksums_file.name == "checksums.txt"

    def test_repr(self):
        """Test that __repr__ returns a meaningful string."""
        config = Config()
        repr_str = repr(config)
        assert "Config" in repr_str
        assert str(config.root) in repr_str
        assert str(config.data_dir) in repr_str