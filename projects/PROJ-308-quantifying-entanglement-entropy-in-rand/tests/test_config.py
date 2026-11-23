"""
Unit tests for the configuration validation module.
"""

import pytest
from config import (
    ConfigError,
    validate_int,
    validate_float,
    validate_random_seed,
    validate_config,
    get_default_config
)


class TestValidateInt:
    def test_valid_int(self):
        assert validate_int(10, 5, 15, "test") == 10

    def test_below_min(self):
        with pytest.raises(ConfigError, match="between 5 and 15"):
            validate_int(4, 5, 15, "test")

    def test_above_max(self):
        with pytest.raises(ConfigError, match="between 5 and 15"):
            validate_int(16, 5, 15, "test")

    def test_non_integer(self):
        with pytest.raises(ConfigError, match="must be an integer"):
            validate_int(10.5, 5, 15, "test")


class TestValidateFloat:
    def test_valid_float(self):
        assert validate_float(0.5, 0.0, 1.0, "test") == 0.5

    def test_valid_int_as_float(self):
        assert validate_float(1, 0.0, 1.0, "test") == 1.0

    def test_below_min(self):
        with pytest.raises(ConfigError, match="between 0.0 and 1.0"):
            validate_float(-0.1, 0.0, 1.0, "test")

    def test_above_max(self):
        with pytest.raises(ConfigError, match="between 0.0 and 1.0"):
            validate_float(1.1, 0.0, 1.0, "test")

    def test_non_number(self):
        with pytest.raises(ConfigError, match="must be a number"):
            validate_float("0.5", 0.0, 1.0, "test")


class TestValidateRandomSeed:
    def test_valid_seed(self):
        assert validate_random_seed(12345) == 12345

    def test_none_seed(self):
        seed = validate_random_seed(None)
        assert isinstance(seed, int)
        assert seed >= 0

    def test_negative_seed(self):
        with pytest.raises(ConfigError, match="must be non-negative"):
            validate_random_seed(-1)

    def test_non_integer_seed(self):
        with pytest.raises(ConfigError, match="must be an integer"):
            validate_random_seed(12.5)


class TestValidateConfig:
    def test_valid_config(self):
        config = validate_config(L=30, delta=0.5, N_real=100, dev_mode=False)
        assert config["L"] == 30
        assert config["delta"] == 0.5
        assert config["N_real"] == 100
        assert config["dev_mode"] is False

    def test_dev_mode_allows_small_L(self):
        config = validate_config(L=10, delta=0.5, N_real=100, dev_mode=True)
        assert config["L"] == 10

    def test_dev_mode_rejects_large_L(self):
        with pytest.raises(ConfigError, match="between 2 and 100"):
            validate_config(L=101, delta=0.5, N_real=100, dev_mode=True)

    def test_standard_mode_rejects_small_L(self):
        with pytest.raises(ConfigError, match="between 20 and 40"):
            validate_config(L=10, delta=0.5, N_real=100, dev_mode=False)

    def test_standard_mode_rejects_large_L(self):
        with pytest.raises(ConfigError, match="between 20 and 40"):
            validate_config(L=50, delta=0.5, N_real=100, dev_mode=False)

    def test_invalid_delta(self):
        with pytest.raises(ConfigError, match="between 0.0 and 1.0"):
            validate_config(L=30, delta=1.5, N_real=100)

    def test_invalid_N_real(self):
        with pytest.raises(ConfigError, match="between 50 and 200"):
            validate_config(L=30, delta=0.5, N_real=10)


class TestGetDefaultConfig:
    def test_defaults(self):
        config = get_default_config()
        assert config["L"] == 30
        assert config["delta"] == 0.2
        assert config["N_real"] == 100
        assert config["dev_mode"] is False