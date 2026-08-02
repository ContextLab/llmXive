import os
import sys
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """
    Test cases to verify the project directory structure is correctly created.
    """

    def test_reports_directory_exists(self):
        """
        T001e: Verify that the reports/ directory exists for final outputs.
        """
        reports_path = Path(".") / "reports"
        assert reports_path.exists(), "reports/ directory must exist for final outputs"
        assert reports_path.is_dir(), "reports/ must be a directory"

    def test_data_subdirectories_exist(self):
        """
        T001b: Verify that data/raw, data/interim, and data/processed exist.
        """
        base = Path(".") / "data"
        assert (base / "raw").exists(), "data/raw must exist"
        assert (base / "interim").exists(), "data/interim must exist"
        assert (base / "processed").exists(), "data/processed must exist"

    def test_code_directory_exists(self):
        """
        T001c: Verify that code/ directory exists with __init__.py.
        """
        code_path = Path(".") / "code"
        assert code_path.exists(), "code/ directory must exist"
        assert (code_path / "__init__.py").exists(), "code/__init__.py must exist"

    def test_tests_subdirectories_exist(self):
        """
        T001d: Verify that tests/unit and tests/integration exist.
        """
        tests_path = Path(".") / "tests"
        assert (tests_path / "unit").exists(), "tests/unit must exist"
        assert (tests_path / "integration").exists(), "tests/integration must exist"

    def test_directory_permissions(self):
        """
        Verify that all required directories are writable.
        """
        required_dirs = [
            Path(".") / "reports",
            Path(".") / "data" / "raw",
            Path(".") / "data" / "interim",
            Path(".") / "data" / "processed",
        ]
        
        for dir_path in required_dirs:
            assert os.access(dir_path, os.W_OK), f"{dir_path} must be writable"
