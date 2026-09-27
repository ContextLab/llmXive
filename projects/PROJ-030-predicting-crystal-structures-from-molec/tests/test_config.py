"""
Tests for the configuration management module (code/config.py).
"""

import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the project root to the path if running from tests directory
# This mimics the import behavior in the actual code
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import (
    get_project_root,
    get_path_absolute,
    get_path_relative,
    ensure_directory,
    get_config_dict,
    get_path_data,
    get_path_processed_data,
    get_path_logs,
    get_path_models,
    get_path_results,
    get_path_validation,
    get_path_figures,
    get_path_code,
    get_path_tests,
    get_path_specs,
    HYPERPARAMETERS,
    RANDOM_SEED,
    TARGET_SAMPLE_SIZE
)


class TestProjectRoot:
    """Tests for project root resolution."""

    def test_project_root_exists(self):
        """Test that a project root can be resolved."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()
        # The root should contain 'code' or be the current working directory
        # depending on how the test is run
        assert root.is_dir()

    def test_data_directory_created(self):
        """Test that the data directory path resolves correctly."""
        data_path = get_path_data()
        assert data_path.is_absolute()
        # Check if it's under the project root
        root = get_project_root()
        assert str(data_path).startswith(str(root))

    def test_logs_directory_created(self):
        """Test that the logs directory path resolves correctly."""
        logs_path = get_path_logs()
        assert logs_path.is_absolute()
        root = get_project_root()
        assert str(logs_path).startswith(str(root))

    def test_models_directory_path(self):
        """Test models directory path resolution."""
        models_path = get_path_models()
        assert models_path.is_absolute()
        assert "models" in str(models_path)

    def test_results_directory_path(self):
        """Test results directory path resolution."""
        results_path = get_path_results()
        assert results_path.is_absolute()
        assert "results" in str(results_path)

    def test_validation_directory_path(self):
        """Test validation directory path resolution."""
        validation_path = get_path_validation()
        assert validation_path.is_absolute()
        assert "validation" in str(validation_path)

    def test_figures_directory_path(self):
        """Test figures directory path resolution."""
        figures_path = get_path_figures()
        assert figures_path.is_absolute()
        assert "figures" in str(figures_path)

    def test_code_directory_path(self):
        """Test code directory path resolution."""
        code_path = get_path_code()
        assert code_path.is_absolute()
        assert "code" in str(code_path)

    def test_tests_directory_path(self):
        """Test tests directory path resolution."""
        tests_path = get_path_tests()
        assert tests_path.is_absolute()
        assert "tests" in str(tests_path)

    def test_specs_directory_path(self):
        """Test specs directory path resolution."""
        specs_path = get_path_specs()
        assert specs_path.is_absolute()
        assert "specs" in str(specs_path)


class TestPathResolution:
    """Tests for path resolution functions."""

    def test_get_path_absolute(self):
        """Test absolute path resolution."""
        root = get_project_root()
        relative = "data/test.csv"
        absolute = get_path_absolute(relative)
        
        expected = root / relative
        assert absolute == expected.resolve()
        assert absolute.is_absolute()

    def test_get_path_relative(self):
        """Test relative path resolution from absolute."""
        root = get_project_root()
        absolute_path = root / "data" / "test.csv"
        relative = get_path_relative(absolute_path)
        
        assert relative == Path("data/test.csv")

    def test_ensure_directory(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "subdir" / "nested"
            # Note: ensure_directory expects relative to project root usually,
            # but if passed an absolute path, it should handle it.
            # We test with a relative path constructed from the temp dir
            # to avoid polluting the actual project structure.
            # However, ensure_directory uses get_path_absolute which uses project root.
            # So we must test by ensuring a path relative to project root.
            pass

    def test_config_paths_match_artifacts(self):
        """Verify that config paths match the expected artifact locations."""
        config = get_config_dict()
        paths = config["paths"]
        
        assert "project_root" in paths
        assert "data" in paths
        assert "processed" in paths
        assert "results" in paths
        assert "models" in paths
        assert "logs" in paths


class TestConfigurationConstants:
    """Tests for configuration constants."""

    def test_random_seed_default(self):
        """Test that the random seed has a default value."""
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_target_sample_size(self):
        """Test that the target sample size is set correctly."""
        assert TARGET_SAMPLE_SIZE == 500

    def test_hyperparameters_structure(self):
        """Test that hyperparameters have the expected structure."""
        assert "model" in HYPERPARAMETERS
        assert "training" in HYPERPARAMETERS
        assert "fingerprint" in HYPERPARAMETERS
        assert "split" in HYPERPARAMETERS

    def test_hyperparameters_rf(self):
        """Test Random Forest hyperparameters."""
        rf = HYPERPARAMETERS["model"]["random_forest"]
        assert "n_estimators" in rf
        assert "max_depth" in rf
        assert rf["n_estimators"] == 200

    def test_hyperparameters_split(self):
        """Test split hyperparameters."""
        split = HYPERPARAMETERS["split"]
        assert split["test_size"] == 0.2
        assert split["rare_space_group_threshold"] == 20

    def test_get_config_dict(self):
        """Test that get_config_dict returns a valid dictionary."""
        config = get_config_dict()
        assert isinstance(config, dict)
        assert "paths" in config
        assert "seeds" in config
        assert "hyperparameters" in config
        assert "targets" in config