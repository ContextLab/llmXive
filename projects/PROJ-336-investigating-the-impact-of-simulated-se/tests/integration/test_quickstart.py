"""
Integration test for the quickstart verification.

The CI workflow expects that ``python -m src.main --dry-run`` exits
with status code 0. This test reproduces that check by invoking the
module as a subprocess and asserting the return code.
"""
import subprocess
import sys
import os
import unittest
from pathlib import Path

class TestQuickstartDryRun(unittest.TestCase):
    """Ensure the dry‑run mode exits cleanly."""

    def test_dry_run_exit_code(self):
        """
        Run ``python -m src.main --dry-run`` and verify it returns 0.
        The test is executed from the project root, mirroring the CI
        environment.
        """
        # Construct the command; use the same Python interpreter that
        # runs the tests to avoid version mismatches.
        cmd = [
            sys.executable,
            "-m",
            "src.main",
            "--dry-run"
        ]

        # Execute the command, capturing stdout/stderr for debugging.
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).resolve().parents[2],  # project root
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # If the command failed, include its output in the assertion
        # message to aid debugging.
        self.assertEqual(
            result.returncode,
            0,
            msg=(
                f"Expected exit code 0, got {result.returncode}\\n"
                f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
            )
        )

if __name__ == "__main__":
    unittest.main()