import os
import sys
import unittest
from pathlib import Path

# Add the parent code directory to the path for imports if running from tests
# Assuming standard layout: projects/PROJ.../tests/
# We need to import from projects/PROJ.../code/
current_dir = Path(__file__).resolve().parent
code_dir = current_dir.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_dirs import main

class TestDirectoryStructure(unittest.TestCase):
    def test_directory_structure_exists(self):
        """
        Verifies that the required directory structure is created or exists.
        This test runs the setup script and then checks for the existence of key directories.
        """
        # Run the setup script to ensure directories exist
        # We capture the return code to ensure it didn't crash
        result = main()
        self.assertEqual(result, 0, "Setup script should return 0")

        # Define the expected paths relative to the current working directory (where the test runs)
        # Note: In a real CI/CD or execution environment, the CWD is the project root.
        # We assume the test is run from the root of the workspace.
        project_root = Path.cwd()
        project_name = "PROJ-498-investigating-the-relationship-between-n"
        base_path = project_root / "projects" / project_name

        expected_dirs = [
            "code",
            "data",
            "tests",
            "data/raw",
            "data/processed",
            "data/metrics",
            "data/trial_level",
            "tests/unit",
            "tests/integration",
            "contracts",
            "logs",
        ]

        for sub_dir in expected_dirs:
            full_path = base_path / sub_dir
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Directory {full_path} should exist."
            )

if __name__ == "__main__":
    unittest.main()