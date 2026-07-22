"""Unit tests for experiment configuration manager."""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

from config import (
    ExperimentConfig,
    get_default_config,
    ensure_directories,
    SENSITIVITY_CUTOFFS,
    STRATIFICATION_THRESHOLDS,
    RANDOM_SEEDS,
)


class TestConstants:
    """Tests for module-level constants."""

    def test_sensitivity_cutoffs_defined(self):
        """Verify SENSITIVITY_CUTOFFS is defined and contains correct values."""
        assert isinstance(SENSITIVITY_CUTOFFS, set)
        assert SENSITIVITY_CUTOFFS == {0.01, 0.05, 0.1}

    def test_stratification_thresholds_defined(self):
        """Verify STRATIFICATION_THRESHOLDS is defined and contains correct values."""
        assert isinstance(STRATIFICATION_THRESHOLDS, set)
        assert STRATIFICATION_THRESHOLDS == {0.5, 5.0}

    def test_random_seeds_defined(self):
        """Verify RANDOM_SEEDS is defined and contains correct values."""
        assert isinstance(RANDOM_SEEDS, list)
        assert RANDOM_SEEDS == [42, 123, 456]


class TestExperimentConfig:
    """Tests for ExperimentConfig class."""

    def test_default_initialization(self):
        """Test ExperimentConfig with default values."""
        config = ExperimentConfig()
        assert config.dataset == "davis"
        assert config.output_dir == "data"
        assert config.batch_size == 1
        assert config.num_workers == 0
        assert config.device == "cpu"
        assert config.seed == 42

    def test_custom_initialization(self):
        """Test ExperimentConfig with custom values."""
        config = ExperimentConfig(
            dataset="youtube_vos",
            output_dir="custom_output",
            batch_size=4,
            num_workers=2,
            device="cuda",
            seed=123,
        )
        assert config.dataset == "youtube_vos"
        assert config.output_dir == "custom_output"
        assert config.batch_size == 4
        assert config.num_workers == 2
        assert config.device == "cuda"
        assert config.seed == 123

    def test_to_dict(self):
        """Test to_dict method returns correct dictionary."""
        config = ExperimentConfig(
            dataset="davis",
            output_dir="data",
            batch_size=1,
            num_workers=0,
            device="cpu",
            seed=42,
        )
        result = config.to_dict()
        expected = {
            "dataset": "davis",
            "output_dir": "data",
            "batch_size": 1,
            "num_workers": 0,
            "device": "cpu",
            "seed": 42,
        }
        assert result == expected


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_experiment_config(self):
        """Verify get_default_config returns an ExperimentConfig instance."""
        config = get_default_config()
        assert isinstance(config, ExperimentConfig)

    def test_returns_default_values(self):
        """Verify get_default_config returns default values."""
        config = get_default_config()
        assert config.dataset == "davis"
        assert config.output_dir == "data"
        assert config.batch_size == 1
        assert config.num_workers == 0
        assert config.device == "cpu"
        assert config.seed == 42


class TestEnsureDirectories:
    """Tests for ensure_directories function."""

    def setup_method(self):
        """Create a temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Remove the temporary directory after tests."""
        shutil.rmtree(self.temp_dir)

    def test_no_args(self):
        """Test ensure_directories with no arguments (no-op)."""
        # Should not raise any exception
        ensure_directories()

    def test_single_string_path(self):
        """Test ensure_directories with a single string path."""
        test_path = os.path.join(self.temp_dir, "test_dir")
        ensure_directories(test_path)
        assert os.path.isdir(test_path)

    def test_single_path_object(self):
        """Test ensure_directories with a single Path object."""
        test_path = Path(self.temp_dir) / "test_dir"
        ensure_directories(test_path)
        assert test_path.is_dir()

    def test_list_of_paths(self):
        """Test ensure_directories with a list of paths."""
        paths = [
            os.path.join(self.temp_dir, "dir1"),
            os.path.join(self.temp_dir, "dir2"),
            os.path.join(self.temp_dir, "dir3"),
        ]
        ensure_directories(paths)
        for p in paths:
            assert os.path.isdir(p)

    def test_variadic_paths(self):
        """Test ensure_directories with variadic arguments."""
        paths = [
            os.path.join(self.temp_dir, "dir1"),
            os.path.join(self.temp_dir, "dir2"),
        ]
        ensure_directories(*paths)
        for p in paths:
            assert os.path.isdir(p)

    def test_mixed_args(self):
        """Test ensure_directories with mixed argument types."""
        path_str = os.path.join(self.temp_dir, "string_dir")
        path_obj = Path(self.temp_dir) / "path_dir"
        list_paths = [
            os.path.join(self.temp_dir, "list_dir1"),
            os.path.join(self.temp_dir, "list_dir2"),
        ]

        ensure_directories(path_str, path_obj, list_paths)

        assert os.path.isdir(path_str)
        assert path_obj.is_dir()
        for p in list_paths:
            assert os.path.isdir(p)

    def test_nested_directories(self):
        """Test ensure_directories creates nested directories."""
        nested_path = os.path.join(self.temp_dir, "level1", "level2", "level3")
        ensure_directories(nested_path)
        assert os.path.isdir(nested_path)

    def test_existing_directory(self):
        """Test ensure_directories handles existing directories gracefully."""
        existing_path = os.path.join(self.temp_dir, "existing")
        os.makedirs(existing_path)
        # Should not raise any exception
        ensure_directories(existing_path)
        assert os.path.isdir(existing_path)

    def test_none_in_list(self):
        """Test ensure_directories handles None values in list."""
        paths = [
            os.path.join(self.temp_dir, "valid_dir"),
            None,
            os.path.join(self.temp_dir, "another_valid_dir"),
        ]
        # Should not raise any exception
        ensure_directories(paths)
        assert os.path.isdir(paths[0])
        assert os.path.isdir(paths[2])