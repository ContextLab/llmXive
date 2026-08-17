import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """Unit tests to verify the existence of required project directories."""

    def test_data_raw_exists(self):
        """Assert that data/raw directory exists."""
        assert os.path.isdir('data/raw'), "Directory 'data/raw' does not exist."

    def test_data_interim_exists(self):
        """Assert that data/interim directory exists."""
        assert os.path.isdir('data/interim'), "Directory 'data/interim' does not exist."

    def test_data_processed_exists(self):
        """Assert that data/processed directory exists."""
        assert os.path.isdir('data/processed'), "Directory 'data/processed' does not exist."

    def test_tests_unit_exists(self):
        """Assert that tests/unit directory exists."""
        assert os.path.isdir('tests/unit'), "Directory 'tests/unit' does not exist."

    def test_tests_integration_exists(self):
        """Assert that tests/integration directory exists."""
        assert os.path.isdir('tests/integration'), "Directory 'tests/integration' does not exist."

    def test_reports_exists(self):
        """Assert that reports directory exists."""
        assert os.path.isdir('reports'), "Directory 'reports' does not exist."

    def test_verification_log_exists(self):
        """Assert that the verification log file exists."""
        assert os.path.isfile('data/.verify_structure.log'), "Verification log 'data/.verify_structure.log' does not exist."

    def test_verification_log_content(self):
        """Assert that the verification log contains 'OK' for all directories."""
        log_path = 'data/.verify_structure.log'
        if not os.path.isfile(log_path):
            pytest.skip("Verification log not found; skipping content check.")
        
        with open(log_path, 'r') as f:
            content = f.read()
        
        expected_dirs = ['data/raw', 'data/interim', 'data/processed', 'tests/unit', 'tests/integration', 'reports']
        for d in expected_dirs:
            assert f"OK {d}" in content, f"Log does not contain 'OK {d}'."