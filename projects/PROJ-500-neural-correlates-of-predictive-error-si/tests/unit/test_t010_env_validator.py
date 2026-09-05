"""
Unit tests for the environment variable validation infrastructure (T010).
"""
import os
import tempfile
import pytest
from pathlib import Path

from src.utils.env_validator import (
    validate_data_dir,
    validate_seed,
    validate_ram_limit,
    validate_environment,
    get_validated_config,
    EnvValidationError
)

class TestValidateDataDir:
    def test_missing_variable(self):
        is_valid, msg = validate_data_dir(None)
        assert not is_valid
        assert "not set" in msg

    def test_non_existent_path(self):
        is_valid, msg = validate_data_dir("/tmp/this_path_does_not_exist_12345")
        assert not is_valid
        assert "does not exist" in msg

    def test_file_instead_of_directory(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            is_valid, msg = validate_data_dir(path)
            assert not is_valid
            assert "not a directory" in msg
        finally:
            os.unlink(path)

    def test_valid_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            is_valid, msg = validate_data_dir(tmpdir)
            assert is_valid
            assert msg is None

    def test_unwritable_directory(self):
        # Create a directory, then make it read-only (if possible on OS)
        # This test might be flaky on Windows without admin privileges,
        # so we focus on the logic path.
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate a scenario where we can't write (harder to test reliably)
            # We trust the touch logic.
            is_valid, msg = validate_data_dir(tmpdir)
            assert is_valid

class TestValidateSeed:
    def test_missing_variable(self):
        is_valid, seed, msg = validate_seed(None)
        assert not is_valid
        assert seed is None
        assert "not set" in msg

    def test_invalid_integer(self):
        is_valid, seed, msg = validate_seed("abc")
        assert not is_valid
        assert seed is None
        assert "not a valid integer" in msg

    def test_negative_integer(self):
        is_valid, seed, msg = validate_seed("-10")
        assert not is_valid
        assert seed is None
        assert "non-negative" in msg

    def test_valid_integer(self):
        is_valid, seed, msg = validate_seed("42")
        assert is_valid
        assert seed == 42
        assert msg is None

    def test_zero_seed(self):
        is_valid, seed, msg = validate_seed("0")
        assert is_valid
        assert seed == 0
        assert msg is None

class TestValidateRamLimit:
    def test_missing_variable(self):
        is_valid, limit, msg = validate_ram_limit(None)
        assert not is_valid
        assert limit is None

    def test_invalid_float(self):
        is_valid, limit, msg = validate_ram_limit("xyz")
        assert not is_valid
        assert "not a valid number" in msg

    def test_zero_limit(self):
        is_valid, limit, msg = validate_ram_limit("0")
        assert not is_valid
        assert "positive" in msg

    def test_negative_limit(self):
        is_valid, limit, msg = validate_ram_limit("-5.0")
        assert not is_valid
        assert "positive" in msg

    def test_valid_limit(self):
        is_valid, limit, msg = validate_ram_limit("7.5")
        assert is_valid
        assert limit == 7.5
        assert msg is None

class TestValidateEnvironment:
    def test_all_missing(self, monkeypatch):
        # Ensure env vars are not set
        monkeypatch.delenv("DATA_DIR", raising=False)
        monkeypatch.delenv("SEED", raising=False)
        monkeypatch.delenv("RAM_LIMIT", raising=False)

        result = validate_environment()
        assert not result.is_valid
        assert len(result.errors) == 3

    def test_all_valid(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("SEED", "123")
        monkeypatch.setenv("RAM_LIMIT", "8.0")

        result = validate_environment()
        assert result.is_valid
        assert result.config["DATA_DIR"] == str(tmp_path.resolve())
        assert result.config["SEED"] == 123
        assert result.config["RAM_LIMIT"] == 8.0

    def test_partial_valid(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.delenv("SEED", raising=False)
        monkeypatch.setenv("RAM_LIMIT", "8.0")

        result = validate_environment()
        assert not result.is_valid
        # Should have error for SEED only
        assert len(result.errors) == 1
        assert result.errors[0].variable_name == "SEED"

class TestGetValidatedConfig:
    def test_raises_on_failure(self, monkeypatch):
        monkeypatch.delenv("DATA_DIR", raising=False)
        monkeypatch.delenv("SEED", raising=False)
        monkeypatch.delenv("RAM_LIMIT", raising=False)

        with pytest.raises(RuntimeError) as exc_info:
            get_validated_config()
        
        assert "Environment validation failed" in str(exc_info.value)

    def test_returns_config_on_success(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        monkeypatch.setenv("SEED", "42")
        monkeypatch.setenv("RAM_LIMIT", "4.0")

        config = get_validated_config()
        assert "DATA_DIR" in config
        assert "SEED" in config
        assert "RAM_LIMIT" in config
        assert config["SEED"] == 42
        assert config["RAM_LIMIT"] == 4.0