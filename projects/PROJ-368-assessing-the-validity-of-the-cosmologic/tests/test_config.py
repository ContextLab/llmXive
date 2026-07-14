"""
Tests for code/config.py configuration constants and paths.
"""

import os
from pathlib import Path
import pytest

# Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.config import (
    PROJECT_ROOT,
    CODE_DIR,
    DATA_DIR,
    TESTS_DIR,
    DOCS_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    SIMULATIONS_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    SIMULATED_MAPS_DIR,
    SIMULATED_CL_DIR,
    RANDOM_SEED,
    NSIDE_ORIGINAL,
    NSIDE_TARGET,
    L_MAX,
    N_SIMULATIONS,
    N_POWER_VALIDATION,
    MIN_SKY_FRACTION,
    L_MIN,
    L_MAX_ANALYSIS,
    MASK_STATS_FILE,
    POWER_VALIDATION_REPORT,
    ensure_directories,
)


class TestConfigPaths:
    """Test that all paths are correctly defined and exist."""

    def test_project_root_is_absolute(self):
        assert PROJECT_ROOT.is_absolute()

    def test_code_dir_exists(self):
        assert CODE_DIR.exists()
        assert CODE_DIR.is_dir()

    def test_data_dir_exists(self):
        assert DATA_DIR.exists()
        assert DATA_DIR.is_dir()

    def test_tests_dir_exists(self):
        assert TESTS_DIR.exists()
        assert TESTS_DIR.is_dir()

    def test_raw_data_dir_exists(self):
        assert RAW_DATA_DIR.exists()
        assert RAW_DATA_DIR.is_dir()

    def test_processed_data_dir_exists(self):
        assert PROCESSED_DATA_DIR.exists()
        assert PROCESSED_DATA_DIR.is_dir()

    def test_simulations_dir_exists(self):
        assert SIMULATIONS_DIR.exists()
        assert SIMULATIONS_DIR.is_dir()

    def test_reports_dir_exists(self):
        assert REPORTS_DIR.exists()
        assert REPORTS_DIR.is_dir()

    def test_figures_dir_exists(self):
        assert FIGURES_DIR.exists()
        assert FIGURES_DIR.is_dir()

    def test_simulated_maps_dir_exists(self):
        assert SIMULATED_MAPS_DIR.exists()
        assert SIMULATED_MAPS_DIR.is_dir()

    def test_simulated_cl_dir_exists(self):
        assert SIMULATED_CL_DIR.exists()
        assert SIMULATED_CL_DIR.is_dir()


class TestConfigConstants:
    """Test that all configuration constants have expected values."""

    def test_random_seed_is_integer(self):
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_nside_original_is_2048(self):
        assert NSIDE_ORIGINAL == 2048

    def test_nside_target_is_128(self):
        assert NSIDE_TARGET == 128

    def test_l_max_is_correct(self):
        # l_max should be 3 * NSIDE_TARGET - 1
        expected = 3 * NSIDE_TARGET - 1
        assert L_MAX == expected
        assert L_MAX_ANALYSIS == expected

    def test_l_min_is_2(self):
        assert L_MIN == 2

    def test_n_simulations_is_positive(self):
        assert N_SIMULATIONS > 0

    def test_n_power_validation_is_positive(self):
        assert N_POWER_VALIDATION > 0

    def test_min_sky_fraction_is_valid(self):
        assert 0 < MIN_SKY_FRACTION < 1

    def test_mask_stats_file_path(self):
        assert MASK_STATS_FILE.name == "mask_stats.json"
        assert MASK_STATS_FILE.parent == PROCESSED_DATA_DIR

    def test_power_validation_report_path(self):
        assert POWER_VALIDATION_REPORT.name == "power_validation.json"
        assert POWER_VALIDATION_REPORT.parent == REPORTS_DIR


class TestEnsureDirectories:
    """Test the ensure_directories function."""

    def test_ensure_directories_creates_missing_dirs(self, tmp_path):
        # Create a temporary project structure
        temp_root = tmp_path / "test_project"
        temp_code = temp_root / "code"
        temp_data = temp_root / "data"
        temp_data_raw = temp_data / "raw"
        temp_data_processed = temp_data / "processed"
        temp_data_sims = temp_data / "simulations"
        temp_data_reports = temp_data / "reports"
        temp_data_figures = temp_data / "figures"
        temp_data_sims_maps = temp_data_sims / "maps"
        temp_data_sims_cl = temp_data_sims / "cl"

        # Temporarily override PROJECT_ROOT for testing
        import code.config as config_module
        original_root = config_module.PROJECT_ROOT
        config_module.PROJECT_ROOT = temp_root
        config_module.DATA_DIR = temp_data
        config_module.RAW_DATA_DIR = temp_data_raw
        config_module.PROCESSED_DATA_DIR = temp_data_processed
        config_module.SIMULATIONS_DIR = temp_data_sims
        config_module.REPORTS_DIR = temp_data_reports
        config_module.FIGURES_DIR = temp_data_figures
        config_module.SIMULATED_MAPS_DIR = temp_data_sims_maps
        config_module.SIMULATED_CL_DIR = temp_data_sims_cl

        try:
            # Call ensure_directories
            config_module.ensure_directories()

            # Verify all directories were created
            assert temp_root.exists()
            assert temp_code.exists()
            assert temp_data.exists()
            assert temp_data_raw.exists()
            assert temp_data_processed.exists()
            assert temp_data_sims.exists()
            assert temp_data_reports.exists()
            assert temp_data_figures.exists()
            assert temp_data_sims_maps.exists()
            assert temp_data_sims_cl.exists()
        finally:
            # Restore original values
            config_module.PROJECT_ROOT = original_root