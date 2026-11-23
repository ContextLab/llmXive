import os
import pytest
from pathlib import Path
import shutil

from code.setup_results_dir import main


class TestSetupResultsDir:
    """Tests for the results directory creation task (T001c)."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure results directory is clean before and after test."""
        results_path = Path("results")
        # Clean up if exists
        if results_path.exists():
            shutil.rmtree(results_path)
        
        yield
        
        # Teardown: remove created directory to keep state clean for other tests
        if results_path.exists():
            shutil.rmtree(results_path)

    def test_creates_results_directory(self):
        """Verify that running main() creates the results directory."""
        results_path = Path("results")
        
        # Directory should not exist initially (due to fixture teardown)
        assert not results_path.exists()
        
        # Run the setup function
        exit_code = main()
        
        # Verify exit code is 0 (success)
        assert exit_code == 0
        
        # Verify directory was created
        assert results_path.exists()
        assert results_path.is_dir()

    def test_directory_is_writable(self):
        """Verify that the created results directory is writable."""
        results_path = Path("results")
        
        # Run setup
        main()
        
        # Try to create a temporary test file
        test_file = results_path / ".test_write_check"
        try:
            test_file.touch()
            assert test_file.exists()
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()

    def test_idempotent_creation(self):
        """Verify that running main() multiple times does not cause errors."""
        results_path = Path("results")
        
        # Run twice
        exit_code_1 = main()
        exit_code_2 = main()
        
        # Both should succeed
        assert exit_code_1 == 0
        assert exit_code_2 == 0
        
        # Directory should still exist
        assert results_path.exists()