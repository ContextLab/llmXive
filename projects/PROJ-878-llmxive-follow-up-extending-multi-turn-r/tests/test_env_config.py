"""
Tests for environment configuration utilities.
"""
import os
import pytest
from code.utils.env_config import validate_environment, get_required_var, get_int_var

class TestEnvConfig:
    """Tests for environment configuration validation."""

    def test_validate_environment_missing_vars(self, monkeypatch):
        """Test validation when required vars are missing."""
        # Clear all required vars
        for var in ["RANDOM_SEED", "MODEL_PATH", "MAX_TURNS", "DATA_PATH_RAW", "DATA_PATH_PROCESSED", "RESULTS_PATH"]:
            monkeypatch.delenv(var, raising=False)

        missing = validate_environment()
        assert len(missing) > 0
        assert "RANDOM_SEED" in missing

    def test_validate_environment_all_set(self, monkeypatch):
        """Test validation when all required vars are set."""
        # Set all required vars
        for var in ["RANDOM_SEED", "MODEL_PATH", "MAX_TURNS", "DATA_PATH_RAW", "DATA_PATH_PROCESSED", "RESULTS_PATH"]:
            monkeypatch.setenv(var, "test_value")

        missing = validate_environment()
        assert len(missing) == 0

    def test_get_required_var_existing(self, monkeypatch):
        """Test getting an existing environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        assert get_required_var("TEST_VAR") == "test_value"

    def test_get_required_var_missing_no_default(self, monkeypatch):
        """Test getting a missing variable without default raises error."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with pytest.raises(ValueError, match="must be set"):
            get_required_var("MISSING_VAR")

    def test_get_required_var_missing_with_default(self, monkeypatch):
        """Test getting a missing variable with default returns default."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert get_required_var("MISSING_VAR", "default_val") == "default_val"

    def test_get_int_var_valid(self, monkeypatch):
        """Test getting an integer variable."""
        monkeypatch.setenv("INT_VAR", "42")
        assert get_int_var("INT_VAR") == 42

    def test_get_int_var_invalid(self, monkeypatch):
        """Test getting an invalid integer variable raises error."""
        monkeypatch.setenv("INT_VAR", "not_a_number")
        with pytest.raises(ValueError, match="must be an integer"):
            get_int_var("INT_VAR")