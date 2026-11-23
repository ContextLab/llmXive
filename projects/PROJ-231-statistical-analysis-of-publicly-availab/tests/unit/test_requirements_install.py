"""
Integration test that verifies the project's pinned requirements can be installed
without error. It runs `python -m pip install -r requirements.txt` and asserts a
zero exit code. The test intentionally uses the same interpreter that runs the
test suite, ensuring that the environment can satisfy the dependencies.
"""
import subprocess
import sys
from pathlib import Path

def test_requirements_install_success() -> None:
    # Locate the project's root (two levels up from this test file)
    project_root = Path(__file__).resolve().parents[2]
    req_file = project_root / "requirements.txt"

    # Run pip install
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True,
        text=True,
    )

    # Debug output in case of failure
    assert result.returncode == 0, (
        f"Pip install failed with exit code {result.returncode}\\n"
        f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
    )