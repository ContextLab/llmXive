"""
Basic test to ensure the install_dependencies script runs without error.
The test does not verify the actual installation of packages (that would
require network access and could be flaky in CI), but it checks that the
script exits with a zero return code and creates the expected log file.
"""
import subprocess
import sys
from pathlib import Path

def test_install_dependencies_script():
    script_path = Path("code", "install_dependencies.py")
    assert script_path.is_file(), "install_dependencies.py must exist"

    # Run the script using the same interpreter
    result = subprocess.run(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # The script should exit with code 0
    assert result.returncode == 0, f"Script failed with {result.returncode}: {result.stderr}"

    # Verify that the log file was created
    log_path = Path("data", "logs", "install_deps.log")
    assert log_path.is_file(), "install_deps.log should be created by the script"
    # Ensure the log contains at least one line (pip output)
    content = log_path.read_text(encoding="utf-8")
    assert len(content.strip()) > 0, "install_deps.log should not be empty"