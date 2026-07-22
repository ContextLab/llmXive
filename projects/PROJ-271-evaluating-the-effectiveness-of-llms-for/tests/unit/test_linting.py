import subprocess
import sys
from pathlib import Path

import pytest

from code.linting_config import run_flake8_check, run_black_format, run_all_checks

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"


class TestLintingConfig:
    """Tests for linting configuration and execution."""

    def test_flake8_importable(self):
        """Verify flake8 is importable and runnable."""
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "flake8 should be installed and runnable"

    def test_black_importable(self):
        """Verify black is importable and runnable."""
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "black should be installed and runnable"

    def test_linting_config_functions_exist(self):
        """Verify all expected functions exist in linting_config."""
        assert callable(run_flake8_check)
        assert callable(run_black_format)
        assert callable(run_all_checks)

    def test_run_all_checks_signature(self):
        """Verify run_all_checks accepts fix parameter."""
        # This test ensures the function signature is correct
        # We don't actually run the full linting here to save time
        import inspect
        sig = inspect.signature(run_all_checks)
        params = list(sig.parameters.keys())
        assert "fix" in params