"""
Unit tests for configuration constants and utilities in code/config.py.
Validates SENSITIVITY_CUTOFFS, STRATIFICATION_THRESHOLDS, and directory handling.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    ExperimentConfig,
    get_default_config,
    get_default_config_dict,
    ensure_directories,
    set_random_seed,
    SENSITIVITY_CUTOFFS,
    STRATIFICATION_THRESHOLDS
)


class TestConfigConstants:
    """Tests for global configuration constants defined in config.py."""

    def test_sensitivity_cutoffs_defined(self):
        """Verify SENSITIVITY_CUTOFFS is defined and is a set."""
        assert SENSITIVITY_CUTOFFS is not None
        assert isinstance(SENSITIVITY_CUTOFFS, set)

    def test_sensitivity_cutoffs_values(self):
        """Verify SENSITIVITY_CUTOFFS contains the expected values {0.01, 0.05, 0.1}."""
        expected = {0.01, 0.05, 0.1}
        assert SENSITIVITY_CUTOFFS == expected

    def test_sensitivity_cutoffs_types(self):
        """Verify all elements in SENSITIVITY_CUTOFFS are floats."""
        for val in SENSITIVITY_CUTOFFS:
            assert isinstance(val, float), f"Value {val} is not a float"

    def test_stratification_thresholds_defined(self):
        """Verify STRATIFICATION_THRESHOLDS is defined and is a set."""
        assert STRATIFICATION_THRESHOLDS is not None
        assert isinstance(STRATIFICATION_THRESHOLDS, set)

    def test_stratification_thresholds_values(self):
        """Verify STRATIFICATION_THRESHOLDS contains the expected values {0.5, 5.0}."""
        expected = {0.5, 5.0}
        assert STRATIFICATION_THRESHOLDS == expected

    def test_stratification_thresholds_types(self):
        """Verify all elements in STRATIFICATION_THRESHOLDS are floats."""
        for val in STRATIFICATION_THRESHOLDS:
            assert isinstance(val, float), f"Value {val} is not a float"


class TestEnsureDirectories:
    """Tests for the ensure_directories utility function."""

    def test_ensure_directories_single_string(self):
        """Test ensure_directories with a single string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "test_dir")
            ensure_directories(target)
            assert os.path.isdir(target)

    def test_ensure_directories_path_object(self):
        """Test ensure_directories with a pathlib.Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test_dir_path"
            ensure_directories(target)
            assert target.is_dir()

    def test_ensure_directories_list_of_strings(self):
        """Test ensure_directories with a list of string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target1 = os.path.join(tmpdir, "dir1")
            target2 = os.path.join(tmpdir, "dir2")
            ensure_directories([target1, target2])
            assert os.path.isdir(target1)
            assert os.path.isdir(target2)

    def test_ensure_directories_list_of_paths(self):
        """Test ensure_directories with a list of Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target1 = Path(tmpdir) / "dir1"
            target2 = Path(tmpdir) / "dir2"
            ensure_directories([target1, target2])
            assert target1.is_dir()
            assert target2.is_dir()

    def test_ensure_directories_nested_creation(self):
        """Test ensure_directories creates nested directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "level1", "level2", "level3")
            ensure_directories(target)
            assert os.path.isdir(target)

    def test_ensure_directories_existing_dir(self):
        """Test ensure_directories does not raise on existing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensure_directories(tmpdir)
            # Should not raise


class TestExperimentConfig:
    """Tests for the ExperimentConfig dataclass."""

    def test_experiment_config_creation(self):
        """Test creating an ExperimentConfig instance with defaults."""
        cfg = ExperimentConfig()
        assert cfg is not None
        assert isinstance(cfg.seed, int)
        assert isinstance(cfg.device, str)

    def test_experiment_config_custom_values(self):
        """Test creating an ExperimentConfig instance with custom values."""
        cfg = ExperimentConfig(seed=42, device="cpu", batch_size=16)
        assert cfg.seed == 42
        assert cfg.device == "cpu"
        assert cfg.batch_size == 16


class TestGetDefaultConfig:
    """Tests for get_default_config and get_default_config_dict."""

    def test_get_default_config_returns_dict(self):
        """Verify get_default_config returns a dictionary."""
        cfg = get_default_config()
        assert isinstance(cfg, dict)

    def test_get_default_config_dict_returns_dict(self):
        """Verify get_default_config_dict returns a dictionary."""
        cfg = get_default_config_dict()
        assert isinstance(cfg, dict)

    def test_config_contains_expected_keys(self):
        """Verify the config dictionary contains expected keys."""
        cfg = get_default_config()
        expected_keys = ["seed", "device", "batch_size", "num_workers"]
        for key in expected_keys:
            assert key in cfg, f"Key '{key}' missing from config"


class TestSetRandomSeed:
    """Tests for set_random_seed function."""

    def test_set_random_seed_no_error(self):
        """Verify set_random_seed executes without raising an exception."""
        try:
            set_random_seed(42)
        except Exception as e:
            pytest.fail(f"set_random_seed raised an exception: {e}")

    def test_set_random_seed_reproducibility(self):
        """Verify set_random_seed produces reproducible results."""
        import numpy as np
        import torch

        set_random_seed(123)
        a = np.random.rand(5)
        b = torch.rand(5)

        set_random_seed(123)
        c = np.random.rand(5)
        d = torch.rand(5)

        assert np.allclose(a, c), "NumPy seed not reproducible"
        assert torch.allclose(b, d), "PyTorch seed not reproducible"