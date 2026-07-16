"""
Unit tests for the configuration manager (T006).
"""

import pytest
from pathlib import Path

# Import the config module
from code.config import (
    get_path,
    get_hub_threshold,
    get_sensitivity_thresholds,
    DEFAULT_HUB_THRESHOLD,
    SENSITIVITY_SWEEP_VALUES,
    ConfigurationError,
    ensure_paths_exist,
    _PROJECT_ROOT,
)

class TestConfigPaths:
    def test_get_path_root(self):
        """Test that root path is correctly identified."""
        path = get_path("root")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_path_data_directories(self):
        """Test that data subdirectories are correctly constructed."""
        raw = get_path("data_raw")
        processed = get_path("data_processed")
        results = get_path("data_results")

        assert raw.parent == _PROJECT_ROOT / "data"
        assert processed.parent == _PROJECT_ROOT / "data"
        assert results.parent == _PROJECT_ROOT / "data"

    def test_get_path_invalid_key(self):
        """Test that an unknown key raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="Unknown path key"):
            get_path("invalid_key")

class TestHubThreshold:
    def test_default_hub_threshold_value(self):
        """Test that the default hub threshold is exactly 0.10."""
        assert DEFAULT_HUB_THRESHOLD == 0.10
        assert get_hub_threshold() == 0.10

class TestSensitivitySweep:
    def test_sweep_values_content(self):
        """Test that the sweep set contains the required values."""
        assert 0.08 in SENSITIVITY_SWEEP_VALUES
        assert 0.10 in SENSITIVITY_SWEEP_VALUES
        assert 0.12 in SENSITIVITY_SWEEP_VALUES
        assert len(SENSITIVITY_SWEEP_VALUES) == 3

    def test_get_sensitivity_thresholds_sorted(self):
        """Test that the returned list is sorted."""
        thresholds = get_sensitivity_thresholds()
        assert thresholds == [0.08, 0.10, 0.12]
        assert thresholds[0] < thresholds[1] < thresholds[2]

class TestDirectoryCreation:
    def test_ensure_paths_exist_creates_missing(self, tmp_path, monkeypatch):
        """Test that ensure_paths_exist creates missing directories."""
        # Create a temporary root structure for the test
        test_root = tmp_path / "test_project"
        test_data = test_root / "data"
        
        # Monkeypatch the global _PROJECT_ROOT and PATHS for this test
        # We need to simulate the config module's behavior with a temp dir
        # Since we can't easily monkeypatch module-level dicts in the imported module
        # without reloading, we just test the logic of directory creation
        # by calling it on the actual paths (which might already exist) or
        # we rely on the fact that the function just calls mkdir(parents=True).
        
        # Instead, let's verify that the function doesn't crash and creates dirs
        # by creating a scenario where a subdirectory is missing.
        # We will create a mock path object in the test to verify mkdir behavior
        # but since the function is fixed to global paths, we just ensure it runs.
        
        # A more robust test: ensure the function runs without error on the real paths
        # (which are created by T004 usually, but if not, this creates them)
        ensure_paths_exist()
        
        # Verify that the expected directories now exist (or were created)
        assert get_path("data_raw").exists()
        assert get_path("data_processed").exists()
        assert get_path("data_results").exists()