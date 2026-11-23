"""
Integration test for the ``code.verify_requirements`` script.

The test simply runs the module as a script and checks that it exits
with status 0 and that the ``results/requirements_install.log`` file
contains the word ``success``.
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths


def test_verify_requirements_success():
    """Run the verification script and ensure it reports success."""
    result = subprocess.run(
        ["python", "-m", "code.verify_requirements"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}"

    log_path = paths.results("requirements_install.log")
    assert log_path.is_file(), "Log file was not created"
    content = log_path.read_text(encoding="utf-8")
    assert "success" in content.lower(), "Log does not contain success marker"


if __name__ == "__main__":
    # Allow manual execution for debugging
    test_verify_requirements_success()
    print("verify_requirements test passed")