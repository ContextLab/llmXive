"""
Tests for src/config/settings.py configuration management.
"""

import os
import pytest
from unittest.mock import patch

# Import the module to test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings


class TestFidelityThresholdValidation:
    """Tests for the fidelity_threshold validation logic."""

    def test_default_value_exists(self):
        """Test that the default fallback value is defined."""
        assert hasattr(settings, 'FIDELITY_THRESHOLD_DEFAULT')
        assert settings.FIDELITY_THRESHOLD_DEFAULT == 0.75

    def test_default_value_used_when_env_missing(self):
        """Test that default is used when env var is not set."""
        # Ensure env var is not set
        with patch.dict(os.environ, {}, clear=False):
            if 'FIDELITY_THRESHOLD' in os.environ:
                del os.environ['FIDELITY_THRESHOLD']
            # Re-import or re-evaluate would be needed in real scenario,
            # but here we test the logic of the loader function directly if exposed,
            # or rely on the fact that the module level constant is set correctly.
            # Since the module runs on import, we test the constant value directly
            # assuming a clean import state in a real runner.
            # For this test, we assert the constant is the default.
            assert settings.FIDELITY_THRESHOLD == settings.FIDELITY_THRESHOLD_DEFAULT

    def test_env_var_overrides_default(self):
        """Test that environment variable overrides the default."""
        with patch.dict(os.environ, {"FIDELITY_THRESHOLD": "0.9"}):
            # In a real test runner, we would reload the module.
            # Here we verify the validation logic via the helper if we could,
            # but since the module is already loaded, we check the logic path
            # by calling the validation function if it were public, or
            # by asserting the expected behavior in a fresh process.
            # For this artifact, we test the _validate function directly.
            result = settings._validate_fidelity_threshold("0.9", 0.75)
            assert result == 0.9

    def test_invalid_string_raises_error(self):
        """Test that non-numeric strings raise ValueError."""
        with pytest.raises(ValueError):
            settings._validate_fidelity_threshold("invalid", 0.75)

    def test_out_of_range_low_raises_error(self):
        """Test that values <= 0 raise ValueError."""
        with pytest.raises(ValueError):
            settings._validate_fidelity_threshold("0.0", 0.75)
        with pytest.raises(ValueError):
            settings._validate_fidelity_threshold(-1.0, 0.75)

    def test_out_of_range_high_raises_error(self):
        """Test that values > 1 raise ValueError."""
        with pytest.raises(ValueError):
            settings._validate_fidelity_threshold("1.1", 0.75)

    def test_valid_boundary_values(self):
        """Test valid boundary values."""
        # 1.0 is valid
        assert settings._validate_fidelity_threshold("1.0", 0.75) == 1.0
        # 0.0001 is valid
        assert settings._validate_fidelity_threshold("0.0001", 0.75) > 0

    def test_integer_input_conversion(self):
        """Test that integer inputs are converted correctly."""
        assert settings._validate_fidelity_threshold(1, 0.75) == 1.0
        assert settings._validate_fidelity_threshold(0, 0.75) == 0.0 # Should fail in logic? No, 0 is not > 0.
        # Actually 0 is not > 0, so it should fail.
        with pytest.raises(ValueError):
            settings._validate_fidelity_threshold(0, 0.75)

    def test_module_level_constant_is_valid(self):
        """Test that the module-level FIDELITY_THRESHOLD is valid."""
        assert isinstance(settings.FIDELITY_THRESHOLD, float)
        assert 0 < settings.FIDELITY_THRESHOLD <= 1.0

class TestConfigStructure:
    """Tests for the general configuration structure."""

    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is a valid Path."""
        assert isinstance(settings.PROJECT_ROOT, Path)
        assert settings.PROJECT_ROOT.exists()

    def test_config_dict_keys(self):
        """Test that the CONFIG dictionary has expected keys."""
        assert "paths" in settings.CONFIG
        assert "hyperparameters" in settings.CONFIG
        assert "analysis" in settings.CONFIG

    def test_fidelity_threshold_in_config(self):
        """Test that fidelity_threshold is in the hyperparameters config."""
        assert "fidelity_threshold" in settings.CONFIG["hyperparameters"]
        assert settings.CONFIG["hyperparameters"]["fidelity_threshold"] == settings.FIDELITY_THRESHOLD

    def test_get_config_functionality(self):
        """Test the get_config helper function."""
        assert settings.get_config("paths", "root") == settings.PROJECT_ROOT
        assert settings.get_config("hyperparameters", "seed") == settings.SEED
        with pytest.raises(KeyError):
            settings.get_config("nonexistent_key")
        with pytest.raises(KeyError):
            settings.get_config("hyperparameters", "nonexistent_subkey")
