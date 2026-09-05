"""Unit tests for code/config.py configuration constants."""
import pytest
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    Config,
    get_config,
    get_data_raw_dir,
    get_data_processed_dir,
    get_data_outputs_dir,
    get_models_dir,
    get_composition_sum_threshold,
    get_max_elements,
    get_vif_threshold,
    get_r2_sensitivity_thresholds,
    get_min_samples_warning,
    get_min_samples_target,
    get_cv_folds,
    get_bootstrap_iterations,
    get_log_level,
    get_log_format
)

class TestConfigConstants:
    """Tests for configuration constants."""

    def test_config_class_exists(self):
        """Test that Config class is defined."""
        assert Config is not None

    def test_max_elements_is_defined(self):
        """Test MAX_ELEMENTS is defined and is an integer."""
        assert hasattr(Config, 'MAX_ELEMENTS')
        assert isinstance(Config.MAX_ELEMENTS, int)
        assert Config.MAX_ELEMENTS == 5

    def test_room_temp_threshold_is_defined(self):
        """Test ROOM_TEMP_THRESHOLD_C is defined and numeric."""
        assert hasattr(Config, 'ROOM_TEMP_THRESHOLD_C')
        assert isinstance(Config.ROOM_TEMP_THRESHOLD_C, (int, float))
        assert Config.ROOM_TEMP_THRESHOLD_C == 25.0

    def test_room_temp_tolerance_is_defined(self):
        """Test ROOM_TEMP_TOLERANCE_C is defined and numeric."""
        assert hasattr(Config, 'ROOM_TEMP_TOLERANCE_C')
        assert isinstance(Config.ROOM_TEMP_TOLERANCE_C, (int, float))
        assert Config.ROOM_TEMP_TOLERANCE_C == 5.0

    def test_composition_sum_threshold_is_defined(self):
        """Test COMPOSITION_SUM_THRESHOLD is explicitly defined as numeric."""
        assert hasattr(Config, 'COMPOSITION_SUM_THRESHOLD')
        assert isinstance(Config.COMPOSITION_SUM_THRESHOLD, (int, float))
        # Must be a specific number, not a placeholder string
        assert Config.COMPOSITION_SUM_THRESHOLD == 95.0
        assert not isinstance(Config.COMPOSITION_SUM_THRESHOLD, str)

    def test_min_n_for_power_is_defined(self):
        """Test MIN_N_FOR_POWER is defined."""
        assert hasattr(Config, 'MIN_N_FOR_POWER')
        assert isinstance(Config.MIN_N_FOR_POWER, int)
        assert Config.MIN_N_FOR_POWER == 50

    def test_target_n_is_defined(self):
        """Test TARGET_N is defined."""
        assert hasattr(Config, 'TARGET_N')
        assert isinstance(Config.TARGET_N, int)
        assert Config.TARGET_N == 100

    def test_get_config_returns_config(self):
        """Test get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)

    def test_getters_return_correct_values(self):
        """Test all getter functions return expected values."""
        assert get_composition_sum_threshold() == 95.0
        assert get_max_elements() == 5
        assert get_vif_threshold() == 5.0
        assert get_min_samples_warning() == 50
        assert get_min_samples_target() == 100
        assert get_cv_folds() == 5
        assert get_bootstrap_iterations() == 100
        assert get_log_level() == "INFO"
        assert get_log_format() == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def test_directory_paths_exist(self):
        """Test that directory paths are valid Path objects."""
        assert isinstance(get_data_raw_dir(), Path)
        assert isinstance(get_data_processed_dir(), Path)
        assert isinstance(get_data_outputs_dir(), Path)
        assert isinstance(get_models_dir(), Path)

    def test_r2_thresholds_is_list(self):
        """Test R2 sensitivity thresholds is a list of floats."""
        thresholds = get_r2_sensitivity_thresholds()
        assert isinstance(thresholds, list)
        assert len(thresholds) > 0
        assert all(isinstance(t, (int, float)) for t in thresholds)