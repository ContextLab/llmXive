"""Unit test for the corruption execution script.

The test simply imports the `run` function to ensure that the module
loads correctly and that the script can be executed without raising
unexpected exceptions when the required data directories exist.

NOTE: This test does **not** verify the actual corruption output;
that is covered by integration‑level tests elsewhere in the project.
"""

import os
import tempfile
import unittest
from unittest import mock

# Import the script's entry point
from exec_corruption import run

class TestExecCorruption(unittest.TestCase):
    @mock.patch("config.ensure_directories")
    @mock.patch("simulators.corruption_injector.main")
    def test_run_calls_dependencies(self, mock_corruption_main, mock_ensure_dirs):
        """Ensure `run` invokes the expected functions."""
        run()
        mock_ensure_dirs.assert_called_once()
        mock_corruption_main.assert_called_once()

    def test_script_can_be_imported(self):
        """Importing the module should not raise."""
        try:
            import exec_corruption  # noqa: F401
        except Exception as e:
            self.fail(f"Importing exec_corruption raised an exception: {e}")

if __name__ == "__main__":
    unittest.main()