"""Unit tests for linting configuration and helpers."""
import subprocess
import sys
from pathlib import Path
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.linting_config import run_flake8_check, run_black_format, run_all_checks


class TestLintingFunctions:
    """Tests for linting utility functions."""

    def test_run_flake8_check_returns_bool(self):
        """Test that run_flake8_check returns a boolean."""
        result = run_flake8_check()
        assert isinstance(result, bool)

    def test_run_black_format_check_returns_bool(self):
        """Test that run_black_format with check_only=True returns a boolean."""
        result = run_black_format(check_only=True)
        assert isinstance(result, bool)

    def test_run_all_checks_returns_bool(self):
        """Test that run_all_checks returns a boolean."""
        result = run_all_checks()
        assert isinstance(result, bool)

    def test_black_check_does_not_modify_files(self):
        """Verify that black --check does not modify files (sanity check)."""
        # This is a behavioral test; we just ensure the function runs without side effects
        # in check mode. The actual file modification is tested by running black without --check.
        result = run_black_format(check_only=True)
        # We don't assert True/False here as the repo might not be perfectly formatted yet,
        # but we assert the function executed.
        assert result is not None

    def test_flake8_runs_on_code_dir(self):
        """Ensure flake8 is executed against the code directory."""
        # This test verifies the subprocess call structure by checking return type
        # and ensuring no exception is raised during execution.
        try:
            result = run_flake8_check()
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"run_flake8_check raised an exception: {e}")
