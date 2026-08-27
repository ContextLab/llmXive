"""
Unit tests for the configuration management module (code/config.py).
"""

import pytest
from pathlib import Path

# Import the config module
# Note: Assuming tests are run from project root or PYTHONPATH is set correctly
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code import config


class TestConfigConstants:
    """Test that configuration constants match the specification (T007)."""

    def test_openneuro_id(self):
        assert config.OPENNEURO_ID == "ds000246"

    def test_n_subjects(self):
        assert config.N_SUBJECTS == 30

    def test_fd_threshold(self):
        assert config.FD_THRESHOLD == 0.5

    def test_mni_template(self):
        assert config.MNI_TEMPLATE == "MNI152NLin2009cAsym"

    def test_threshold_default(self):
        assert config.THRESHOLD_DEFAULT == 0.20

    def test_memory_limit(self):
        assert config.MEMORY_LIMIT_GB == 6.5

    def test_atlas_name(self):
        assert config.ATLAS_NAME == "Schaefer_200Parcels_7Networks"

    def test_n_regions(self):
        assert config.N_REGIONS == 200

    def test_threshold_sweep_values(self):
        expected = [0.10, 0.20, 0.30]
        assert config.THRESHOLD_SWEEP_VALUES == expected


class TestConfigPaths:
    """Test that derived paths are correct."""

    def test_project_root_exists(self):
        assert isinstance(config.PROJECT_ROOT, Path)
        assert config.PROJECT_ROOT.exists()

    def test_data_dirs_exist(self):
        # The validate_config function ensures these exist
        assert config.DATA_RAW_DIR.exists()
        assert config.DATA_PROCESSED_DIR.exists()
        assert config.FIGURES_DIR.exists()


class TestConfigValidation:
    """Test the validation logic."""

    def test_validate_config_success(self):
        # Should not raise
        config.validate_config()

    def test_validate_config_invalid_n_subjects(self):
        # Temporarily override to test validation logic
        original = config.N_SUBJECTS
        try:
            config.N_SUBJECTS = 150  # Invalid
            with pytest.raises(ValueError, match="N_SUBJECTS.*must be between 1 and 100"):
                config.validate_config()
        finally:
            config.N_SUBJECTS = original

    def test_validate_config_invalid_threshold(self):
        original = config.THRESHOLD_DEFAULT
        try:
            config.THRESHOLD_DEFAULT = 1.5  # Invalid (> 1.0)
            with pytest.raises(ValueError, match="THRESHOLD_DEFAULT.*must be between 0 and 1"):
                config.validate_config()
        finally:
            config.THRESHOLD_DEFAULT = original
