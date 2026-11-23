"""
Integration test to verify the full directory structure setup.
This test ensures that the script can be run and produces the expected file system state.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestDirectoryStructureIntegration:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for integration testing."""
        temp_root = tempfile.mkdtemp()
        yield temp_root
        shutil.rmtree(temp_root)

    def test_script_execution_creates_structure(self, temp_project_root):
        """
        Test that running the setup script creates the correct directory structure.
        """
        # Change to temp directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)

            # Run the script
            result = subprocess.run(
                ["python", "-m", "code.utils.setup_directories"],
                capture_output=True,
                text=True,
                check=True
            )

            # Verify output
            assert "Directory structure setup complete" in result.stdout

            # Verify directories exist
            data_raw = Path("data/raw")
            data_processed = Path("data/processed")
            data_results = Path("data/results")

            assert data_raw.is_dir(), f"Expected {data_raw} to exist"
            assert data_processed.is_dir(), f"Expected {data_processed} to exist"
            assert data_results.is_dir(), f"Expected {data_results} to exist"

        finally:
            os.chdir(original_cwd)
