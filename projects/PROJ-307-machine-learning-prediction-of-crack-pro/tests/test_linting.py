"""
Simple test to ensure that the linting script exits with status 0.
The CI will also run the script directly, but this provides a quick
verification during local pytest runs.
"""

import subprocess
import pathlib

def test_lint_script_exit_code():
    script_path = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "run_lint.sh"
    result = subprocess.run([str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Linter failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"