"""
Test that the quick‑start sample command runs correctly.

The verification for task T003 requires that executing:
    python -m code.main --run-sample
finishes quickly and prints exactly “Sample run completed”.

This test launches the module in a subprocess, captures stdout,
and asserts that the expected string appears.  A timeout of 30 seconds
is enforced to guarantee the command terminates promptly.
"""

import subprocess
import sys
import os
import unittest
from pathlib import Path

class TestQuickstartSampleRun(unittest.TestCase):
    def test_sample_run_output(self):
        # Build the command: use the current interpreter to run the module
        cmd = [sys.executable, "-m", "code.main", "--run-sample"]
        # Run with a timeout of 30 seconds
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            cwd=Path(__file__).resolve().parents[1]  # project root
        )
        # Decode output
        stdout = result.stdout.decode(errors="ignore").strip()
        # The script should exit with code 0
        self.assertEqual(result.returncode, 0, msg=f"Non‑zero exit code: {result.stderr.decode()}")
        # Verify the exact expected output
        self.assertIn("Sample run completed", stdout)

if __name__ == "__main__":
    unittest.main()