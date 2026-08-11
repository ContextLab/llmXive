import os
import sys
from pathlib import Path
import pytest
import shutil
import tempfile

# We need to add the code directory to the path to import setup_directories
# Assuming tests are run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from setup_directories import create_directories, verify_directories, generate_verification_log

class TestDirectoryStructure:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Setup: Create a temporary directory to simulate the project root.
        Teardown: Clean up the temporary directory.
        """
        self.original_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_directories_creates_all_paths(self):
        """Test that create_directories creates all required paths."""
        paths = create_directories()
        
        expected_paths = [
            'data/raw',
            'data/interim',
            'data/processed',
            'tests/unit',
            'tests/integration',
            'reports'
        ]
        
        assert len(paths) == len(expected_paths)
        for expected in expected_paths:
            assert expected in paths
            assert Path(expected).is_dir()

    def test_verify_directories_returns_true_for_existing(self):
        """Test that verify_directories returns True when all dirs exist."""
        create_directories()
        paths = [
            'data/raw',
            'data/interim',
            'data/processed',
            'tests/unit',
            'tests/integration',
            'reports'
        ]
        assert verify_directories(paths) is True

    def test_verify_directories_returns_false_for_missing(self):
        """Test that verify_directories returns False if a dir is missing."""
        # Create only some directories
        Path('data/raw').mkdir(parents=True)
        
        paths = [
            'data/raw',
            'data/interim', # This one is missing
            'data/processed',
            'tests/unit',
            'tests/integration',
            'reports'
        ]
        assert verify_directories(paths) is False

    def test_generate_verification_log_creates_file(self):
        """Test that generate_verification_log creates the log file."""
        paths = create_directories()
        log_path = 'data/.verify_structure.log'
        
        generate_verification_log(paths, log_path)
        
        assert Path(log_path).is_file()
        
        # Check content format
        with open(log_path, 'r') as f:
            content = f.read()
        
        for p in paths:
            assert p in content
            # The log format is "OK path" or "FAILED path", so we check for the path itself
            # and ensure the status is present.
            assert f"OK {p}" in content or f"FAILED {p}" in content

    def test_full_workflow(self):
        """Test the full workflow: create -> verify -> log."""
        # Create
        created = create_directories()
        
        # Verify
        assert verify_directories(created) is True
        
        # Log
        log_path = 'data/.verify_structure.log'
        generate_verification_log(created, log_path)
        
        # Final assertions
        assert Path(log_path).exists()
        assert Path('data/raw').exists()
        assert Path('data/interim').exists()
        assert Path('data/processed').exists()
        assert Path('tests/unit').exists()
        assert Path('tests/integration').exists()
        assert Path('reports').exists()
        
        # Verify log content specifically for T001 requirement
        with open(log_path, 'r') as f:
            content = f.read()
        
        for p in created:
            assert f"OK {p}" in content, f"Log missing OK status for {p}"

    def test_verification_log_all_ok(self):
        """
        Specific test to ensure that if directories are created successfully,
        the log file contains ONLY 'OK' entries and no 'FAILED' entries.
        This satisfies the T001 requirement: 'If data/.verify_structure.log ... 
        does not contain 'OK' for all directories, the test MUST fail'.
        """
        paths = create_directories()
        log_path = 'data/.verify_structure.log'
        generate_verification_log(paths, log_path)
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Skip header lines if any, look for status lines
        status_lines = [line.strip() for line in lines if line.strip().startswith(('OK', 'FAILED'))]
        
        assert len(status_lines) == len(paths), "Number of status lines must match number of paths"
        
        for line in status_lines:
            assert line.startswith("OK"), f"Found a FAILED entry in log: {line}"
            # Extract path from "OK path"
            parts = line.split(" ", 1)
            assert len(parts) == 2, f"Invalid log format: {line}"
            path_name = parts[1]
            assert path_name in paths, f"Path in log not in expected list: {path_name}"
