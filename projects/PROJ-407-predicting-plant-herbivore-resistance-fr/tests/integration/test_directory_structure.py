import os
import subprocess
import tempfile
from pathlib import Path
import pytest


class TestDirectoryStructureIntegration:
    """Integration tests for the complete directory structure setup."""

    def test_full_directory_creation_via_script(self, tmp_path):
        """Test that the setup script creates the complete directory structure."""
        # Run the setup script
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_directories.py"
        result = subprocess.run(
            ["python", str(script_path)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )
        
        # Verify script ran successfully
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Verify all required directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/interim",
            "data/processed",
            "data/results",
            "tests/unit",
            "tests/integration",
            "tests/contract",
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} not found after script execution"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_directory_structure_matches_spec(self, tmp_path):
        """Verify the created structure matches the specification exactly."""
        # Run setup
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_directories.py"
        subprocess.run(["python", str(script_path)], cwd=str(tmp_path), check=True)
        
        # Define expected structure
        expected_structure = {
            "code": [],
            "data": ["raw", "interim", "processed", "results"],
            "tests": ["unit", "integration", "contract"],
        }
        
        # Verify structure
        for parent, children in expected_structure.items():
            parent_path = tmp_path / parent
            assert parent_path.exists(), f"Parent directory {parent} missing"
            
            for child in children:
                child_path = parent_path / child
                assert child_path.exists(), f"Child directory {parent}/{child} missing"
                assert child_path.is_dir(), f"{parent}/{child} is not a directory"

    def test_no_unexpected_files_created(self, tmp_path):
        """Verify that only the specified directories are created, no extra files."""
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_directories.py"
        subprocess.run(["python", str(script_path)], cwd=str(tmp_path), check=True)
        
        # Get all items in root
        root_items = list(tmp_path.iterdir())
        
        # Expected top-level directories
        expected_top_level = {
            "code", "data", "tests"
        }
        
        actual_top_level = {item.name for item in root_items}
        
        assert actual_top_level == expected_top_level, \
            f"Unexpected top-level items: {actual_top_level - expected_top_level}"

    def test_directory_permissions(self, tmp_path):
        """Verify directories have correct permissions (writable)."""
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_directories.py"
        subprocess.run(["python", str(script_path)], cwd=str(tmp_path), check=True)
        
        test_dirs = ["code", "data/raw", "tests/unit"]
        
        for dir_name in test_dirs:
            dir_path = tmp_path / dir_name
            # Try to create a temporary file to verify writability
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                pytest.fail(f"Directory {dir_name} is not writable")

    def test_idempotency(self, tmp_path):
        """Verify that running the script multiple times doesn't cause errors."""
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_directories.py"
        
        # Run twice
        result1 = subprocess.run(["python", str(script_path)], cwd=str(tmp_path), capture_output=True, text=True)
        result2 = subprocess.run(["python", str(script_path)], cwd=str(tmp_path), capture_output=True, text=True)
        
        assert result1.returncode == 0, f"First run failed: {result1.stderr}"
        assert result2.returncode == 0, f"Second run failed: {result2.stderr}"
        
        # Verify structure is still correct
        required_dirs = [
            "code", "data/raw", "data/interim", "data/processed",
            "data/results", "tests/unit", "tests/integration", "tests/contract"
        ]
        
        for dir_name in required_dirs:
            assert (tmp_path / dir_name).exists()