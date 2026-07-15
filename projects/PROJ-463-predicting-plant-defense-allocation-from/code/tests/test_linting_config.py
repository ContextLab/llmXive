import subprocess
import sys
from pathlib import Path
import pytest


def test_black_config_valid():
    """Verify that Black configuration is valid and can format a dummy file."""
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "pyproject.toml"

    # Create a temporary dummy Python file to test formatting
    dummy_file = project_root / "dummy_format_test.py"
    try:
        dummy_file.write_text("x=1+2\n")

        # Run black in check mode (no write) to verify config is valid
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--config", str(config_path), str(dummy_file)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Exit code 1 is expected if the file is not formatted (which it isn't),
        # but we want to ensure the command ran and config was parsed without error.
        # Exit code 0 would mean it's already formatted.
        # Exit code >= 2 means a configuration error.
        assert result.returncode in (0, 1), f"Black config error: {result.stderr}"

    finally:
        if dummy_file.exists():
            dummy_file.unlink()


def test_ruff_config_valid():
    """Verify that Ruff configuration is valid and can lint a dummy file."""
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "pyproject.toml"

    # Create a temporary dummy Python file to test linting
    dummy_file = project_root / "dummy_lint_test.py"
    try:
        # Intentionally include a style error (unused import) to test linting
        dummy_file.write_text("import os\nx = 1\n")

        # Run ruff check to verify config is valid
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", str(config_path), str(dummy_file)],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Ruff returns 0 if no issues found, 1 if issues found, 2 if config error.
        # We expect issues (unused import) so 1 is acceptable, 0 is acceptable (if ignore list changed),
        # but 2 is a failure.
        assert result.returncode != 2, f"Ruff config error: {result.stderr}"

    finally:
        if dummy_file.exists():
            dummy_file.unlink()