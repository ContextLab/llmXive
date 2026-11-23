"""Test that the project's ``code/`` package passes flake8 linting.

The test invokes the ``code/run_flake8.py`` script as a subprocess.
It asserts that the script exits with a zero return code, which
indicates that no flake8 errors are present.
"""
import subprocess
import sys
from pathlib import Path

def test_code_is_flake8_clean():
    """Run the flake8 helper script and ensure it succeeds."""
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "code" / "run_flake8.py"

    # Use the same Python interpreter that is running the tests.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # If flake8 finds errors the script exits with a non‑zero code.
    assert result.returncode == 0, (
        f"flake8 reported errors:\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )
