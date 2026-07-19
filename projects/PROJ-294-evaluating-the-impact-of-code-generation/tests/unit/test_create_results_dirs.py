"""
tests/unit/test_create_results_dirs.py

Unit tests for the create_results_dirs module.
Verifies that the required directory structure is created correctly.
"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# We need to import the module under test.
# Since the project structure puts code/ at the root relative to tests/,
# we add the parent of tests to the path if necessary, or assume code/ is importable.
# Given the task constraints, we assume 'code' is in the path or we import relative to project root.
# The prompt says artifacts are relative to project root.
# Let's assume the test runner adds the project root to sys.path.
# We will import the function directly if possible, or mock the os calls.

# To make this runnable in a standard environment where 'code' is a directory:
import sys
import importlib.util

# Try to load the module dynamically to avoid path issues in different runners
spec = importlib.util.spec_from_file_location("create_results_dirs", "code/create_results_dirs.py")
create_results_dirs_module = importlib.util.module_from_spec(spec)
sys.modules["create_results_dirs"] = create_results_dirs_module
spec.loader.exec_module(create_results_dirs_module)

ensure_results_directories = create_results_dirs_module.ensure_results_directories


class TestCreateResultsDirs(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to act as the project root."""
        self.test_dir = tempfile.mkdtemp()
        # Change to the test directory to simulate the project root
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        # Ensure 'results' is not present initially
        if os.path.exists("results"):
            shutil.rmtree("results")

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_creates_results_and_figures(self):
        """Test that ensure_results_directories creates 'results' and 'results/figures'."""
        # Call the function
        success = ensure_results_directories()

        # Assert success
        self.assertTrue(success)

        # Assert directories exist
        self.assertTrue(os.path.isdir("results"))
        self.assertTrue(os.path.isdir(os.path.join("results", "figures")))

    def test_handles_existing_directories(self):
        """Test that the function succeeds if directories already exist."""
        # Pre-create the directories
        os.makedirs("results/figures", exist_ok=True)

        # Call the function
        success = ensure_results_directories()

        # Assert success
        self.assertTrue(success)

        # Assert they are still there
        self.assertTrue(os.path.isdir("results"))
        self.assertTrue(os.path.isdir(os.path.join("results", "figures")))

    def test_creates_missing_figures_only(self):
        """Test that the function creates 'figures' if 'results' exists but 'figures' does not."""
        # Pre-create 'results' only
        os.makedirs("results", exist_ok=True)

        # Call the function
        success = ensure_results_directories()

        # Assert success
        self.assertTrue(success)

        # Assert 'figures' was created
        self.assertTrue(os.path.isdir(os.path.join("results", "figures")))


if __name__ == "__main__":
    unittest.main()