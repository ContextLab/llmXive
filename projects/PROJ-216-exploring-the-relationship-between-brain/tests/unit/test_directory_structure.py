import os
import sys
import pytest
from pathlib import Path
import shutil

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_directories import create_directories, verify_directories, generate_verification_log

class TestDirectoryStructure:
    """Unit tests for directory initialization logic."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and clean up after."""
        # Create a temporary base directory for testing
        self.test_base = Path('tests/temp_test_dirs')
        self.test_base.mkdir(parents=True, exist_ok=True)
        
        # Define paths relative to test base
        self.test_paths = [
            str(self.test_base / 'data' / 'raw'),
            str(self.test_base / 'data' / 'interim'),
            str(self.test_base / 'data' / 'processed'),
            str(self.test_base / 'tests' / 'unit'),
            str(self.test_base / 'tests' / 'integration'),
            str(self.test_base / 'reports')
        ]
        self.test_log = str(self.test_base / 'data' / '.verify_structure.log')

        yield

        # Cleanup: Remove test base directory
        if self.test_base.exists():
            shutil.rmtree(self.test_base)

    def test_create_directories_creates_all_paths(self):
        """Test that create_directories creates all specified paths."""
        create_directories(self.test_paths)
        
        for p in self.test_paths:
            assert os.path.isdir(p), f"Directory {p} was not created"

    def test_verify_directories_returns_true_when_all_exist(self):
        """Test that verify_directories returns True when all directories exist."""
        # First ensure directories exist
        create_directories(self.test_paths)
        
        result = verify_directories(self.test_paths)
        assert result is True

    def test_verify_directories_returns_false_when_missing(self):
        """Test that verify_directories returns False if a directory is missing."""
        # Create all but one
        create_directories(self.test_paths[:-1])
        
        result = verify_directories(self.test_paths)
        assert result is False

    def test_generate_verification_log_creates_file_with_entries(self):
        """Test that generate_verification_log creates the log file with correct content."""
        # Ensure directories exist first
        create_directories(self.test_paths)
        
        generate_verification_log(self.test_paths, self.test_log)
        
        assert os.path.isfile(self.test_log), "Verification log file was not created"
        
        with open(self.test_log, 'r') as f:
            content = f.read()
        
        # Verify all paths are in the log
        for p in self.test_paths:
            assert p in content, f"Path {p} not found in verification log"
        
        # Verify format (path:timestamp)
        lines = content.strip().split('\n')
        assert len(lines) == len(self.test_paths), "Log does not contain entries for all paths"
        
        for line in lines:
            assert ':' in line, f"Log entry '{line}' does not contain a timestamp separator"

    def test_full_workflow(self):
        """Test the complete workflow: create, verify, and log."""
        create_directories(self.test_paths)
        assert verify_directories(self.test_paths) is True
        
        generate_verification_log(self.test_paths, self.test_log)
        assert os.path.isfile(self.test_log)
        
        # Re-verify after log generation (should still be True)
        assert verify_directories(self.test_paths) is True