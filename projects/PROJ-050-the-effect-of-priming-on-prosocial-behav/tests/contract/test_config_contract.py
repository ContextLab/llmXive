"""Contract tests for configuration interface."""
import pytest

from code.config import (
    PROJECT_ROOT,
    TARGET_N,
    ALPHA,
    EFFECT_SIZE_D,
    MIN_GROUP_SIZE,
)


class TestConfigContract:
    """Test suite for configuration contract."""

    def test_all_required_config_values_exist(self):
        """Test that all required configuration values are defined."""
        required_values = {
            "PROJECT_ROOT": PROJECT_ROOT,
            "TARGET_N": TARGET_N,
            "ALPHA": ALPHA,
            "EFFECT_SIZE_D": EFFECT_SIZE_D,
            "MIN_GROUP_SIZE": MIN_GROUP_SIZE,
        }

        for name, value in required_values.items():
            assert value is not None, f"Configuration value {name} is None"

    def test_config_types_match_contract(self):
        """Test that configuration values have correct types."""
        from pathlib import Path

        assert isinstance(PROJECT_ROOT, Path), "PROJECT_ROOT must be a Path"
        assert isinstance(TARGET_N, int), "TARGET_N must be an integer"
        assert isinstance(ALPHA, float), "ALPHA must be a float"
        assert isinstance(EFFECT_SIZE_D, float), "EFFECT_SIZE_D must be a float"
        assert isinstance(MIN_GROUP_SIZE, int), "MIN_GROUP_SIZE must be an integer"

    def test_config_values_are_reasonable(self):
        """Test that configuration values are within expected ranges."""
        # TARGET_N should be positive
        assert TARGET_N > 0, "TARGET_N must be positive"

        # ALPHA should be between 0 and 1
        assert 0 < ALPHA < 1, "ALPHA must be between 0 and 1"

        # EFFECT_SIZE_D should be positive
        assert EFFECT_SIZE_D > 0, "EFFECT_SIZE_D must be positive"

        # MIN_GROUP_SIZE should be positive
        assert MIN_GROUP_SIZE > 0, "MIN_GROUP_SIZE must be positive"

    def test_project_root_is_absolute(self):
        """Test that PROJECT_ROOT is an absolute path."""
        assert PROJECT_ROOT.is_absolute(), "PROJECT_ROOT must be an absolute path"
