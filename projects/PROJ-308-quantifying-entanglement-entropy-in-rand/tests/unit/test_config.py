"""
Unit tests for the configuration validation module.
"""

import pytest
from code.config import (
    ConfigError,
    validate_int,
    validate_float,
    validate_random_seed,
    validate_config,
    get_default_config
)


class TestValidateInt:
    def test_valid_int(self):
        result = validate_int(25, 20, 40, "L")
        assert result == 25

    def test_boundary_min(self):
        result = validate_int(20, 20, 40, "L")
        assert result == 20

    def test_boundary_max(self):
        result = validate_int(40, 20, 40, "L")
        assert result == 40

    def test_below_min(self):
        with pytest.raises(ConfigError, match="must be between 20 and 40"):
            validate_int(19, 20, 40, "L")

    def test_above_max(self):
        with pytest.raises(ConfigError, match="must be between 20 and 40"):
            validate_int(41, 20, 40, "L")

    def test_not_integer(self):
        with pytest.raises(ConfigError, match="must be an integer"):
            validate_int(25.5, 20, 40, "L")


class TestValidateFloat:
    def test_valid_float(self):
        result = validate_float(0.5, 0.0, 1.0, "delta")
        assert result == 0.5

    def test_boundary_min(self):
        result = validate_float(0.0, 0.0, 1.0, "delta")
        assert result == 0.0

    def test_boundary_max(self):
        result = validate_float(1.0, 0.0, 1.0, "delta")
        assert result == 1.0

    def test_below_min(self):
        with pytest.raises(ConfigError, match="must be between 0.0 and 1.0"):
            validate_float(-0.1, 0.0, 1.0, "delta")

    def test_above_max(self):
        with pytest.raises(ConfigError, match="must be between 0.0 and 1.0"):
            validate_float(1.1, 0.0, 1.0, "delta")

    def test_not_number(self):
        with pytest.raises(ConfigError, match="must be a number"):
            validate_float("0.5", 0.0, 1.0, "delta")


class TestValidateRandomSeed:
    def test_valid_seed(self):
        result = validate_random_seed(42)
        assert result == 42

    def test_none_seed(self):
        result = validate_random_seed(None)
        assert isinstance(result, int)
        assert result >= 0

    def test_negative_seed(self):
        with pytest.raises(ConfigError, match="must be non-negative"):
            validate_random_seed(-1)

    def test_invalid_type(self):
        with pytest.raises(ConfigError, match="must be an integer or None"):
            validate_random_seed("42")


class TestValidateConfig:
    def test_valid_config(self):
        config = validate_config(L=30, delta=0.2, N_real=100, random_seed=42)
        assert config["L"] == 30
        assert config["delta"] == 0.2
        assert config["N_real"] == 100
        assert config["random_seed"] == 42
        assert config["dev_mode"] is False

    def test_dev_mode_allows_small_L(self):
        # dev_mode=True should allow L=10 (toy model)
        config = validate_config(L=10, delta=0.2, N_real=100, random_seed=42, dev_mode=True)
        assert config["L"] == 10
        assert config["dev_mode"] is True

    def test_dev_mode_allows_large_L(self):
        # dev_mode=True should allow L=100 (extended range)
        config = validate_config(L=100, delta=0.2, N_real=100, random_seed=42, dev_mode=True)
        assert config["L"] == 100

    def test_normal_mode_rejects_small_L(self):
        with pytest.raises(ConfigError, match="must be between 20 and 40"):
            validate_config(L=10, delta=0.2, N_real=100, random_seed=42, dev_mode=False)

    def test_invalid_delta(self):
        with pytest.raises(ConfigError, match="must be between 0.0 and 1.0"):
            validate_config(L=30, delta=1.5, N_real=100, random_seed=42)

    def test_invalid_N_real(self):
        with pytest.raises(ConfigError, match="must be between 50 and 200"):
            validate_config(L=30, delta=0.2, N_real=10, random_seed=42)

    def test_auto_seed_generation(self):
        config = validate_config(L=30, delta=0.2, N_real=100, random_seed=None)
        assert isinstance(config["random_seed"], int)
        assert config["random_seed"] >= 0


class TestGetDefaultConfig:
    def test_default_values(self):
        config = get_default_config()
        assert config["L"] == 30
        assert config["delta"] == 0.2
        assert config["N_real"] == 100
        assert config["random_seed"] is None
        assert config["dev_mode"] is False
