"""
Integration tests for the setup_tests module.
These tests verify the end-to-end functionality of creating the tests directory hierarchy.
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_tests import setup_tests_directories, main


class TestSetupTestsIntegration:
    """Integration test cases for the setup_tests module."""

    def test_full_directory_hierarchy_creation(self, tmp_path):
        """Test the complete creation of the tests directory hierarchy."""
        # Create the directory structure
        result = setup_tests_directories(tmp_path)
        
        # Verify all directories exist
        tests_dir = tmp_path / "tests"
        unit_dir = tmp_path / "tests" / "unit"
        integration_dir = tmp_path / "tests" / "integration"
        
        assert tests_dir.exists()
        assert tests_dir.is_dir()
        assert unit_dir.exists()
        assert unit_dir.is_dir()
        assert integration_dir.exists()
        assert integration_dir.is_dir()
        
        # Verify they are in the result
        assert tests_dir in result
        assert unit_dir in result
        assert integration_dir in result

    def test_write_operations_in_all_directories(self, tmp_path):
        """Test that we can perform write operations in all created directories."""
        result = setup_tests_directories(tmp_path)
        
        for directory in result:
            # Create a test file
            test_file = directory / "integration_test.txt"
            test_content = "Integration test content"
            
            with open(test_file, "w") as f:
                f.write(test_content)
            
            # Verify the file was created
            assert test_file.exists()
            
            # Read back and verify content
            with open(test_file, "r") as f:
                content = f.read()
            assert content == test_content
            
            # Clean up
            test_file.unlink()

    def test_nested_directory_structure(self, tmp_path):
        """Test that nested directory structures are created correctly."""
        nested_path = tmp_path / "project" / "src"
        
        result = setup_tests_directories(nested_path)
        
        expected_dirs = [
            nested_path / "tests",
            nested_path / "tests" / "unit",
            nested_path / "tests" / "integration"
        ]
        
        for expected_dir in expected_dirs:
            assert expected_dir.exists()
            assert expected_dir.is_dir()
            assert expected_dir in result

    def test_idempotency(self, tmp_path):
        """Test that running the setup multiple times is idempotent."""
        # First run
        result1 = setup_tests_directories(tmp_path)
        assert len(result1) == 3
        
        # Second run - should not fail or create duplicates
        result2 = setup_tests_directories(tmp_path)
        assert len(result2) == 3
        
        # Verify the same directories exist
        tests_dir = tmp_path / "tests"
        unit_dir = tmp_path / "tests" / "unit"
        integration_dir = tmp_path / "tests" / "integration"
        
        assert tests_dir.exists()
        assert unit_dir.exists()
        assert integration_dir.exists()

    def test_cli_execution(self, tmp_path):
        """Test running the setup script via command line."""
        script_path = Path(__file__).parent.parent.parent / "code" / "setup_tests.py"
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path), "--base-path", str(tmp_path), "--verbose"],
            capture_output=True,
            text=True
        )
        
        # Check that it succeeded
        assert result.returncode == 0, f"Script failed with: {result.stderr}"
        
        # Verify directories were created
        tests_dir = tmp_path / "tests"
        unit_dir = tmp_path / "tests" / "unit"
        integration_dir = tmp_path / "tests" / "integration"
        
        assert tests_dir.exists()
        assert unit_dir.exists()
        assert integration_dir.exists()
        
        # Check output contains expected messages
        assert "Verified:" in result.stdout
        assert "setup complete" in result.stdout.lower()
