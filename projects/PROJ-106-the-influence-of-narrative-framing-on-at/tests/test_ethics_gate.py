"""
Tests for the Ethics Gate module (T004).
"""

import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code import _00_ethics_gate as ethics_gate


class TestEthicsGate:
    """Test cases for IRB approval checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_project_root = Path(self.temp_dir.name)
        self.mock_ethics_dir = self.mock_project_root / "data" / "ethics"
        self.mock_ethics_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporarily override the module's constants for testing
        self.original_ethics_dir = ethics_gate.ETHICS_DIR
        ethics_gate.ETHICS_DIR = self.mock_ethics_dir

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
        # Restore original constant
        ethics_gate.ETHICS_DIR = self.original_ethics_dir

    def test_approval_exists_returns_true(self):
        """Test that existing approval file returns True."""
        approval_file = self.mock_ethics_dir / "IRB_APPROVAL.txt"
        approval_file.write_text("IRB Approval #12345 - Valid")
        
        result = ethics_gate.check_ethics_approval()
        assert result is True

    def test_missing_approval_raises_runtime_error(self):
        """Test that missing approval file raises RuntimeError."""
        with pytest.raises(RuntimeError) as excinfo:
            ethics_gate.check_ethics_approval()
        
        assert "IRB approval file" in str(excinfo.value)
        assert "missing" in str(excinfo.value)
        assert "Constitution VI" in str(excinfo.value)

    def test_empty_approval_file_raises_runtime_error(self):
        """Test that empty approval file raises RuntimeError."""
        approval_file = self.mock_ethics_dir / "IRB_APPROVAL.txt"
        approval_file.write_text("")  # Empty file
        
        with pytest.raises(RuntimeError) as excinfo:
            ethics_gate.check_ethics_approval()
        
        assert "empty" in str(excinfo.value).lower()

    def test_missing_ethics_directory_raises_file_not_found(self):
        """Test that missing ethics directory raises FileNotFoundError."""
        # Remove the ethics directory
        self.mock_ethics_dir.rmdir()
        
        with pytest.raises(FileNotFoundError) as excinfo:
            ethics_gate.check_ethics_approval()
        
        assert "Ethics directory not found" in str(excinfo.value)

    def test_main_success_exits_zero(self, capsys):
        """Test that main() exits with 0 on success."""
        approval_file = self.mock_ethics_dir / "IRB_APPROVAL.txt"
        approval_file.write_text("IRB Approval #12345 - Valid")
        
        # Mock sys.exit to capture the exit code
        exit_code = None
        def mock_exit(code):
            nonlocal exit_code
            exit_code = code
            raise SystemExit(code)
        
        original_exit = sys.exit
        sys.exit = mock_exit
        
        try:
            ethics_gate.main()
        except SystemExit:
            pass
        finally:
            sys.exit = original_exit
        
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out

    def test_main_missing_approval_exits_nonzero(self, capsys):
        """Test that main() exits with non-zero on missing approval."""
        # Ensure no file exists
        
        exit_code = None
        def mock_exit(code):
            nonlocal exit_code
            exit_code = code
            raise SystemExit(code)
        
        original_exit = sys.exit
        sys.exit = mock_exit
        
        try:
            ethics_gate.main()
        except SystemExit:
            pass
        finally:
            sys.exit = original_exit
        
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "BLOCKED" in captured.err