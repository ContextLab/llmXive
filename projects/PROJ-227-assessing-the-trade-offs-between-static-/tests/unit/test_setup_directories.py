"""
Unit tests for setup_directories module.
Verifies that T001 creates the required directory structure.
"""
import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to import the module from the code directory
# Adjust sys.path to include the project root or code directory
import sys
from pathlib import Path as PathLib

# Add the project root to sys.path if not already present
project_root = PathLib(__file__).parent.parent.parent
code_dir = project_root / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-" / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import main

class TestSetupDirectories:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """
        Setup: Create a temporary directory to act as the project root.
        Teardown: Clean up is handled by pytest's tmp_path.
        """
        self.original_cwd = PathLib.cwd()
        self.test_root = tmp_path / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-"
        self.test_root.mkdir(parents=True)
        
        # Change to the test root to simulate the script running there
        os.chdir(self.test_root)
        
        yield
        
        # Restore original directory
        os.chdir(self.original_cwd)

    def test_creates_required_directories(self):
        """
        Test that the script creates all directories specified in T001.
        Required: data/raw, data/processed, state, code, tests
        """
        # Run the main function
        result = main()
        
        # Assert the function returned success
        assert result == 0, "Script should exit with code 0"

        # Define the expected paths relative to the test root
        expected_dirs = [
            "data/raw",
            "data/processed",
            "state",
            "code",
            "tests",
            "data/logs", # Added for pipeline logging support
            "specs",
            "contracts",
            "figures",
        ]

        for rel_path in expected_dirs:
            full_path = self.test_root / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} exists but is not a directory."

    def test_idempotency(self):
        """
        Test that running the script twice does not cause errors.
        """
        # Run once
        result1 = main()
        assert result1 == 0

        # Run again
        result2 = main()
        assert result2 == 0
        
        # Verify directories still exist
        assert (self.test_root / "code").exists()
        assert (self.test_root / "data" / "raw").exists()