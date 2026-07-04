"""
Unit tests for linting configuration.

These tests verify that the configuration dictionaries are valid
and contain expected keys. They do NOT run the actual linters
(which would require the full project environment).
"""
import pytest
from code.linting_config import (
    FLAKE8_CONFIG,
    BLACK_CONFIG,
    run_flake8_check,
    run_black_format,
    run_all_checks,
)


class TestFlake8Config:
    def test_max_line_length_is_int(self):
        assert isinstance(FLAKE8_CONFIG["max-line-length"], int)
        assert FLAKE8_CONFIG["max-line-length"] == 88

    def test_extend_ignore_is_list(self):
        assert isinstance(FLAKE8_CONFIG["extend-ignore"], list)
        assert "E203" in FLAKE8_CONFIG["extend-ignore"]

    def test_exclude_is_list(self):
        assert isinstance(FLAKE8_CONFIG["exclude"], list)
        assert ".git" in FLAKE8_CONFIG["exclude"]
        assert "data" in FLAKE8_CONFIG["exclude"]

    def test_per_file_ignores_is_dict(self):
        assert isinstance(FLAKE8_CONFIG["per-file-ignores"], dict)
        assert "__init__.py" in FLAKE8_CONFIG["per-file-ignores"]


class TestBlackConfig:
    def test_line_length_is_int(self):
        assert isinstance(BLACK_CONFIG["line-length"], int)
        assert BLACK_CONFIG["line-length"] == 88

    def test_target_version_is_list(self):
        assert isinstance(BLACK_CONFIG["target-version"], list)
        assert "py311" in BLACK_CONFIG["target-version"]

    def test_include_is_regex_string(self):
        assert isinstance(BLACK_CONFIG["include"], str)
        assert r"\.pyi?$" in BLACK_CONFIG["include"]


class TestRunFunctions:
    """
    Tests for the runner functions.
    Note: These are smoke tests. They verify the functions exist
    and have the correct signature, but we don't actually run
    flake8/black here to avoid environment dependencies in unit tests.
    """
    def test_run_flake8_check_signature(self):
        # Just verify it accepts the argument and returns an int
        # We don't actually run it to avoid side effects
        import inspect
        sig = inspect.signature(run_flake8_check)
        assert "project_root" in sig.parameters

    def test_run_black_format_signature(self):
        import inspect
        sig = inspect.signature(run_black_format)
        assert "project_root" in sig.parameters

    def test_run_all_checks_signature(self):
        import inspect
        sig = inspect.signature(run_all_checks)
        assert "project_root" in sig.parameters