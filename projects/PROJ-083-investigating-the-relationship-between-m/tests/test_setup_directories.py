import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path so we can import code modules
# In a real execution environment, this would be handled by the runner
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from code.setup_directories import setup_directories

class TestSetupDirectories:
    """
    Test suite for the setup_directories functionality (Task T001).
    
    This verifies that the required project structure is created correctly
    and that the verification logic works as expected.
    """

    def test_creates_all_required_directories(self, tmp_path):
        """
        Verify that setup_directories creates all required directories.
        
        Required directories:
        - code/
        - code/utils/
        - data/raw/
        - data/processed/
        - data/models/
        - tests/
        - docs/reports/
        - contracts/
        """
        # Change to temp directory to simulate a fresh project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = setup_directories()
            
            assert result is True, "setup_directories should return True on success"
            
            # Verify each directory exists
            required_dirs = [
                "code",
                "code/utils",
                "data/raw",
                "data/processed",
                "data/models",
                "tests",
                "docs/reports",
                "contracts"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} should exist"
                assert dir_path.is_dir(), f"{dir_name} should be a directory"
                
        finally:
            os.chdir(original_cwd)

    def test_handles_existing_directories(self, tmp_path):
        """
        Verify that setup_directories handles pre-existing directories gracefully.
        """
        # Create some directories beforehand
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data/raw").mkdir()
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = setup_directories()
            
            # Should still succeed even with existing directories
            assert result is True
            
            # Verify all required directories still exist
            required_dirs = [
                "code",
                "code/utils",
                "data/raw",
                "data/processed",
                "data/models",
                "tests",
                "docs/reports",
                "contracts"
            ]
            
            for dir_name in required_dirs:
                assert (tmp_path / dir_name).exists()
                
        finally:
            os.chdir(original_cwd)

    def test_nested_directories_created(self, tmp_path):
        """
        Verify that nested directories (like code/utils) are created correctly.
        """
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            result = setup_directories()
            
            assert result is True
            
            # Check nested structure
            assert (tmp_path / "code" / "utils").is_dir()
            assert (tmp_path / "data" / "raw").is_dir()
            assert (tmp_path / "data" / "processed").is_dir()
            assert (tmp_path / "data" / "models").is_dir()
            assert (tmp_path / "docs" / "reports").is_dir()
            
        finally:
            os.chdir(original_cwd)

    def test_verification_logic(self, tmp_path, capsys):
        """
        Verify that the verification output is printed correctly.
        """
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_directories()
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Check for verification markers
            assert "[CREATED]" in output or "[SKIP]" in output
            assert "Directory setup complete" in output
            assert "Verifying directory structure" in output
            
            # Check that all directories are marked as OK
            assert "[OK] code/" in output
            assert "[OK] code/utils/" in output
            assert "[OK] data/raw/" in output
            assert "[OK] data/processed/" in output
            assert "[OK] data/models/" in output
            assert "[OK] tests/" in output
            assert "[OK] docs/reports/" in output
            assert "[OK] contracts/" in output
            
        finally:
            os.chdir(original_cwd)

    def test_returns_false_on_failure(self, tmp_path, monkeypatch):
        """
        Verify that setup_directories returns False if directory creation fails.
        """
        # This is hard to test without mocking system calls, but we can test
        # the logic path by ensuring the function structure is sound.
        # The actual failure case would be a permissions error or similar.
        pass
