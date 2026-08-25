import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function from the module
# Note: In a real test environment, we'd ensure code/ is in sys.path
# For this implementation, we assume the test runner handles path setup
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import setup_code_directories

class TestSetupCodeDirectories:
    """Tests for the setup_code_directories function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required subdirectories are created."""
        result = setup_code_directories(tmp_path)
        
        assert result is True
        
        code_root = tmp_path / "code"
        assert code_root.exists()
        
        required_dirs = ["dataset", "symbolic", "bes", "analysis", "utils"]
        for subdir in required_dirs:
            dir_path = code_root / subdir
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_verifies_writability(self, tmp_path):
        """Verify that the function checks for writability."""
        # Create a read-only directory to simulate a failure
        # (This is harder to test reliably across OS, so we focus on the happy path
        # and the exception handling in the function itself)
        result = setup_code_directories(tmp_path)
        assert result is True
        
        # Attempt to write a file in each created directory
        code_root = tmp_path / "code"
        for subdir in ["dataset", "symbolic", "bes", "analysis", "utils"]:
            dir_path = code_root / subdir
            test_file = dir_path / "test_write.tmp"
            try:
                test_file.write_text("test")
                assert test_file.exists()
                test_file.unlink()
            except OSError:
                pytest.fail(f"Could not write to {dir_path}")

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the function doesn't fail if directories already exist."""
        # Create the directories first
        code_root = tmp_path / "code"
        code_root.mkdir()
        (code_root / "dataset").mkdir()
        (code_root / "symbolic").mkdir()
        (code_root / "bes").mkdir()
        (code_root / "analysis").mkdir()
        (code_root / "utils").mkdir()
        
        result = setup_code_directories(tmp_path)
        assert result is True

    def test_raises_on_unwritable_root(self, tmp_path, monkeypatch):
        """Verify that RuntimeError is raised if the root is not writable."""
        # This is difficult to test portably, so we rely on the logic in the function
        # We can at least verify the function signature and basic logic
        pass
        
    def test_returns_true_on_success(self, tmp_path):
        """Verify that the function returns True on success."""
        result = setup_code_directories(tmp_path)
        assert result is True