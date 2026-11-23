import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """
    Unit tests for T001: Initialize Data Directory Structure.
    Verifies that the required directories exist and the log file is generated correctly.
    """

    def test_directories_exist(self):
        """Verify that all required directories exist after T001 execution."""
        expected_dirs = [
            'data/raw',
            'data/interim',
            'data/processed',
            'data/external',
            'tests/unit',
            'tests/integration',
            'reports'
        ]
        
        missing = []
        for d in expected_dirs:
            if not os.path.isdir(d):
                missing.append(d)
        
        assert len(missing) == 0, f"Missing directories: {missing}"

    def test_verification_log_exists(self):
        """Verify that the verification log file exists."""
        log_path = "data/.verify_structure.log"
        assert os.path.isfile(log_path), f"Verification log file missing: {log_path}"

    def test_verification_log_content(self):
        """Verify that the verification log contains 'OK' for all expected directories."""
        log_path = "data/.verify_structure.log"
        expected_dirs = [
            'data/raw',
            'data/interim',
            'data/processed',
            'data/external',
            'tests/unit',
            'tests/integration',
            'reports'
        ]

        assert os.path.isfile(log_path), f"Verification log file missing: {log_path}"

        with open(log_path, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.startswith('OK')]
            found = [l.split(' ', 1)[1] for l in lines]

        missing = set(expected_dirs) - set(found)
        assert len(missing) == 0, f"Log file missing entries for: {missing}"