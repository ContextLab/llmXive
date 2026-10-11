"""
Integration test for the quickstart documentation.

The quickstart specifies that the command ``python -m src.main --dry-run``
must exit with status 0. This test runs that command in a subprocess and
asserts the exit code.
"""

import subprocess
import sys
import os
import unittest
from pathlib import Path

class TestQuickstartDryRun(unittest.TestCase):
    """Verify that the dry‑run command succeeds."""

    def test_dry_run_exits_successfully(self):
        """Run ``python -m src.main --dry-run`` and check return code."""
        # Resolve the path to the project root (the directory containing this test file's parent)
        project_root = Path(__file__).resolve().parents[2]

        # Build the command: python -m src.main --dry-run
        cmd = [sys.executable, "-m", "src.main", "--dry-run"]

        # Execute the command in the project root to ensure module resolution works.
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Debug output in case of failure
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)

        # Assert that the process exited with code 0.
        self.assertEqual(
            result.returncode,
            0,
            msg="Dry‑run command did not exit cleanly (expected 0).",
        )

if __name__ == "__main__":
    unittest.main()