import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so we can import the setup script logic
# assuming this test runs from the project root or code/tests
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from setup_directories import main

class TestSetupDirectories:
    def test_directories_exist(self, tmp_path, monkeypatch):
        """Verify that the script creates the required directory structure."""
        # Monkeypatch the base_dir detection to use our temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # We need to simulate the script running from code/
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            os.chdir(code_dir)
            
            # Run the main function
            result = main()
            assert result == 0

            # Verify directories exist
            required_dirs = [
                "code", "data", "data/raw", "data/intermediate",
                "data/processed", "data/provenance", "data/results",
                "tests", "tests/unit", "tests/integration", "tests/contract"
            ]
            
            for dir_name in required_dirs:
                target = Path(dir_name)
                assert target.exists(), f"Directory {target} was not created"
                assert target.is_dir(), f"{target} exists but is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path, monkeypatch):
        """Verify that running the script twice does not error."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            os.chdir(code_dir)
            
            # Run twice
            main()
            main()
            
            # Should still exist
            assert (Path("data") / "raw").exists()
        finally:
            os.chdir(original_cwd)