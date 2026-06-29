"""
Unit tests for code/config.py validation logic.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.config import (
    validate_int,
    validate_float,
    validate_random_seed,
    validate_config,
    get_default_config,
    ConfigError
)


class TestValidateInt:
    """Tests for validate_int function."""

    def test_valid_int_in_range(self):
        """Test that valid integers in range are accepted."""
        result = validate_int(30, 20, 40, "L")
        assert result == 30
        assert isinstance(result, int)

    def test_valid_int_at_bounds(self):
        """Test boundary values are accepted."""
        assert validate_int(20, 20, 40, "L") == 20
        assert validate_int(40, 20, 40, "L") == 40

    def test_invalid_int_below_min(self):
        """Test that integers below min raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_int(19, 20, 40, "L")
        assert "must be between 20 and 40" in str(exc_info.value)

    def test_invalid_int_above_max(self):
        """Test that integers above max raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_int(41, 20, 40, "L")
        assert "must be between 20 and 40" in str(exc_info.value)

    def test_invalid_type(self):
        """Test that non-integers raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_int(30.5, 20, 40, "L")
        assert "must be an integer" in str(exc_info.value)

    def test_string_input(self):
        """Test that string input raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_int("30", 20, 40, "L")
        assert "must be an integer" in str(exc_info.value)


class TestValidateFloat:
    """Tests for validate_float function."""

    def test_valid_float_in_range(self):
        """Test that valid floats in range are accepted."""
        result = validate_float(0.5, 0.0, 1.0, "delta")
        assert result == 0.5
        assert isinstance(result, float)

    def test_valid_int_as_float(self):
        """Test that integers are converted to float."""
        result = validate_float(0, 0.0, 1.0, "delta")
        assert result == 0.0
        assert isinstance(result, float)

    def test_valid_float_at_bounds(self):
        """Test boundary values are accepted."""
        assert validate_float(0.0, 0.0, 1.0, "delta") == 0.0
        assert validate_float(1.0, 0.0, 1.0, "delta") == 1.0

    def test_invalid_float_below_min(self):
        """Test that floats below min raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_float(-0.1, 0.0, 1.0, "delta")
        assert "must be between 0.0 and 1.0" in str(exc_info.value)

    def test_invalid_float_above_max(self):
        """Test that floats above max raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_float(1.1, 0.0, 1.0, "delta")
        assert "must be between 0.0 and 1.0" in str(exc_info.value)

    def test_invalid_type(self):
        """Test that non-numbers raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_float("0.5", 0.0, 1.0, "delta")
        assert "must be a number" in str(exc_info.value)


class TestValidateRandomSeed:
    """Tests for validate_random_seed function."""

    def test_valid_seed(self):
        """Test that valid seeds are accepted."""
        assert validate_random_seed(42) == 42
        assert validate_random_seed(0) == 0
        assert validate_random_seed(2**32 - 1) == 2**32 - 1

    def test_none_generates_seed(self):
        """Test that None generates a random seed."""
        seed = validate_random_seed(None)
        assert isinstance(seed, int)
        assert seed >= 0

    def test_negative_seed(self):
        """Test that negative seeds raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_random_seed(-1)
        assert "must be non-negative" in str(exc_info.value)

    def test_invalid_type(self):
        """Test that non-integers raise ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_random_seed(42.5)
        assert "must be an integer or None" in str(exc_info.value)


class TestValidateConfig:
    """Tests for the main validate_config function."""

    def test_valid_config(self):
        """Test that valid configuration is accepted."""
        config = validate_config(L=30, delta=0.5, N_real=100, random_seed=42)
        assert config["L"] == 30
        assert config["delta"] == 0.5
        assert config["N_real"] == 100
        assert config["random_seed"] == 42

    def test_valid_config_with_none_seed(self):
        """Test that None seed generates a random one."""
        config = validate_config(L=30, delta=0.5, N_real=100, random_seed=None)
        assert config["L"] == 30
        assert config["delta"] == 0.5
        assert config["N_real"] == 100
        assert isinstance(config["random_seed"], int)

    def test_invalid_L(self):
        """Test that invalid L raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config(L=15, delta=0.5, N_real=100)
        assert "L" in str(exc_info.value)

    def test_invalid_delta(self):
        """Test that invalid delta raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config(L=30, delta=1.5, N_real=100)
        assert "delta" in str(exc_info.value)

    def test_invalid_N_real(self):
        """Test that invalid N_real raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config(L=30, delta=0.5, N_real=10)
        assert "N_real" in str(exc_info.value)

    def test_invalid_random_seed(self):
        """Test that invalid random_seed raises ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config(L=30, delta=0.5, N_real=100, random_seed=-5)
        assert "random_seed" in str(exc_info.value)

    def test_boundary_values(self):
        """Test configuration with boundary values."""
        config = validate_config(L=20, delta=0.0, N_real=50, random_seed=0)
        assert config["L"] == 20
        assert config["delta"] == 0.0
        assert config["N_real"] == 50
        assert config["random_seed"] == 0

        config = validate_config(L=40, delta=1.0, N_real=200, random_seed=1000)
        assert config["L"] == 40
        assert config["delta"] == 1.0
        assert config["N_real"] == 200
        assert config["random_seed"] == 1000


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_default_values(self):
        """Test that default values are correct."""
        config = get_default_config()
        assert config["L"] == 30
        assert config["delta"] == 0.2
        assert config["N_real"] == 100
        assert config["random_seed"] is None

    def test_default_config_validates(self):
        """Test that default config passes validation."""
        config = get_default_config()
        # This should not raise
        validated = validate_config(
            config["L"],
            config["delta"],
            config["N_real"],
            config["random_seed"]
        )
        assert validated["L"] == 30
        assert validated["delta"] == 0.2
        assert validated["N_real"] == 100