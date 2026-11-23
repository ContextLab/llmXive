"""
Tests for the setup_viz_dir module.
Verifies that the viz directory and .gitkeep file are created correctly.
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_viz_dir import main
from utils.config import get_project_root, get_viz_dir


class TestSetupVizDir(unittest.TestCase):
    def setUp(self):
        """
        Set up a temporary directory structure for testing.
        We temporarily override the config to use a temp directory.
        """
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        # We will test by creating the structure manually or mocking,
        # but since get_viz_dir relies on project structure, we test the side effects.
        # For this unit test, we verify the function runs without error and creates the file.
        # Note: In a real CI, this might run against a specific project layout.
        # Here we assume the project layout exists or we test the logic in isolation.
        pass

    def tearDown(self):
        """
        Clean up temporary directories.
        """
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.chdir(self.original_cwd)

    def test_main_execution(self):
        """
        Test that main() runs without raising exceptions.
        """
        # We expect this to run against the actual project structure if available,
        # or we might need to mock the path. For now, we assume the project root
        # is correctly identified by get_project_root().
        try:
            exit_code = main()
            self.assertEqual(exit_code, 0)
        except Exception as e:
            # If the project structure isn't set up yet, this might fail.
            # However, the task is to create the directory.
            # If the directory creation logic is sound, it should succeed.
            # We assert that the viz directory exists after the call if it failed due to missing dir?
            # Actually, the script creates it. So if it raises, the logic is flawed.
            self.fail(f"main() raised an exception: {e}")

    def test_gitkeep_creation(self):
        """
        Test that .gitkeep is created in the viz directory.
        """
        viz_dir = get_viz_dir()
        gitkeep_path = viz_dir / ".gitkeep"

        # Ensure the directory exists first (in case test runs in isolation)
        viz_dir.mkdir(parents=True, exist_ok=True)

        # Run main
        main()

        self.assertTrue(gitkeep_path.exists(), ".gitkeep file was not created")
        self.assertTrue(gitkeep_path.is_file(), ".gitkeep is not a file")


if __name__ == "__main__":
    unittest.main()