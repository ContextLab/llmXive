"""
Test for the CI limits checker script (code/ci_limits.py).

This test creates a deliberately violating monitoring CSV file,
runs the script, and verifies that it exits with status code 1
and prints an appropriate violation message to stderr.
"""

import subprocess
import sys
import shutil
from pathlib import Path

# Import the project-specific path utilities
from llmxive_toolkit import paths

def test_ci_limits_violations(tmp_path):
    """
    Overwrite the project's results/monitoring.csv with a CSV that
    exceeds both RAM and time limits, then invoke the CI limits
    script and check that it fails as expected.
    """
    # Resolve the monitoring CSV path used by the script
    monitoring_path = paths.results("monitoring.csv")

    # Backup the original monitoring file if it exists
    backup_path = None
    if monitoring_path.exists():
        backup_path = monitoring_path.with_suffix(".bak")
        shutil.copy2(monitoring_path, backup_path)

    try:
        # Write a violating CSV: one step exceeding RAM and total time
        violating_content = (
            "step,wall_time_s,peak_ram_bytes\n"
            "violating_step,30000,8000000000\n"
        )
        monitoring_path.write_text(violating_content)

        # Run the ci_limits script using the same Python interpreter
        result = subprocess.run(
            [sys.executable, "code/ci_limits.py"],
            cwd=Path(__file__).parents[1],  # project root
            capture_output=True,
            text=True,
        )

        # The script should exit with code 1 due to violations
        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}. "
            f"Stderr: {result.stderr}"
        )

        # Verify that the expected violation messages appear in stderr
        assert "SC-003 violation" in result.stderr, "Missing SC-003 violation message"
        assert "SC-004 violation" in result.stderr, "Missing SC-004 violation message"

    finally:
        # Restore the original monitoring file if we backed it up
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(monitoring_path))
        else:
            # If there was no original file, remove the temporary one
            if monitoring_path.exists():
                monitoring_path.unlink()