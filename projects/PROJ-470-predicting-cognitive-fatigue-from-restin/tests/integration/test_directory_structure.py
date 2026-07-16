import os
import sys
import tempfile
from pathlib import Path
import subprocess
import pytest

class TestDirectoryStructureIntegration:
    def test_full_directory_structure_via_subprocess(self, tmp_path):
        """
        Integration test: Run the setup script as a subprocess and verify
        the complete directory structure is created.
        """
        # Prepare environment
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Find the setup script
            script_path = Path(__file__).parent.parent.parent / "code" / "setup_structure.py"
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Check exit code
            assert result.returncode == 0, f"Script failed with:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            
            # Verify expected structure
            base_project_dir = tmp_path / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin"
            
            required_paths = [
                "data/raw",
                "data/processed",
                "data/analysis",
                "code",
                "tests/unit",
                "tests/integration",
                "docs"
            ]
            
            for rel_path in required_paths:
                full_path = base_project_dir / rel_path
                assert full_path.exists(), f"Missing required path: {rel_path}"
                assert full_path.is_dir(), f"Path is not a directory: {rel_path}"
                
            # Check that the base project directory name is correct
            assert base_project_dir.name == "PROJ-470-predicting-cognitive-fatigue-from-restin"
            assert base_project_dir.parent.name == "projects"
            
        finally:
            os.chdir(original_cwd)

    def test_output_contains_verification(self, tmp_path):
        """
        Integration test: Verify the script outputs verification messages.
        """
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            script_path = Path(__file__).parent.parent.parent / "code" / "setup_structure.py"
            
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                cwd=tmp_path
            )
            
            # Check for verification messages in output
            assert "Created" in result.stdout or "already exists" in result.stdout
            assert "setup complete" in result.stdout.lower()
            assert "verified successfully" in result.stdout.lower()
            
        finally:
            os.chdir(original_cwd)