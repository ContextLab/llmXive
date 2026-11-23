import os
import subprocess
import sys
from pathlib import Path
import pytest

class TestSetupIntegration:
    """Integration tests for project structure setup."""

    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project root for testing."""
        return tmp_path

    def test_full_setup_execution(self, temp_project_root):
        """Test running the full setup script creates all required artifacts."""
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            # Run the setup script
            result = subprocess.run(
                [sys.executable, "code/setup_structure.py"],
                cwd=temp_project_root,
                capture_output=True,
                text=True
            )
            
            # Check exit code
            assert result.returncode == 0, f"Setup failed: {result.stderr}"
            
            # Verify directories exist
            required_dirs = [
                "code",
                "code/utils",
                "data/raw/repos",
                "data/processed",
                "tests/unit",
                "tests/integration",
                "state",
                "logs"
            ]
            
            for dir_path in required_dirs:
                assert (temp_project_root / dir_path).is_dir(), f"Directory missing: {dir_path}"
            
            # Verify .gitkeep files exist
            gitkeep_count = 0
            for root, dirs, files in os.walk(temp_project_root):
                for file in files:
                    if file == ".gitkeep":
                        gitkeep_count += 1
            
            assert gitkeep_count == 8, f"Expected 8 .gitkeep files, found {gitkeep_count}"
            
        finally:
            os.chdir(original_cwd)

    def test_setup_script_output_contains_verification(self, temp_project_root):
        """Test that the setup script output contains verification messages."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            
            # Run the setup script
            result = subprocess.run(
                [sys.executable, "code/setup_structure.py"],
                cwd=temp_project_root,
                capture_output=True,
                text=True
            )
            
            # Check that verification messages are present
            assert "Verified:" in result.stdout, "Verification messages not found in output"
            assert "Created directory:" in result.stdout, "Directory creation messages not found"
            assert "Created .gitkeep:" in result.stdout, "Gitkeep creation messages not found"
            
        finally:
            os.chdir(original_cwd)
