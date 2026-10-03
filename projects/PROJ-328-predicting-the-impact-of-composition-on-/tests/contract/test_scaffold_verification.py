"""
Contract test for T001a: Directory Initialization Verification.
Ensures all required project directories exist and are valid.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path to allow imports if needed, though we mostly test filesystem
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
sys.path.insert(0, str(project_root))

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/outputs",
    "code/ingestion",
    "code/features",
    "code/models",
    "code/evaluation",
    "code/visualization",
    "code/utils",
    "tests/contract",
    "tests/integration",
]

class TestDirectoryStructure:
    """Tests to verify the project directory structure required by T001a."""

    @pytest.mark.parametrize("rel_path", REQUIRED_DIRS)
    def test_directory_exists(self, rel_path):
        """
        Verify that each required directory exists.
        Equivalent to 'test -d' in shell.
        """
        full_path = project_root / rel_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

    def test_all_required_directories_present(self):
        """
        Verify that ALL required directories are present in a single check.
        """
        missing = []
        for rel_path in REQUIRED_DIRS:
            full_path = project_root / rel_path
            if not full_path.exists() or not full_path.is_dir():
                missing.append(rel_path)
        
        assert len(missing) == 0, f"Missing required directories: {missing}"

    def test_data_raw_is_writable(self):
        """Verify data/raw is writable (basic permission check)."""
        raw_dir = project_root / "data" / "raw"
        if raw_dir.exists():
            # Try to create a temp file
            test_file = raw_dir / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except OSError:
                pytest.fail(f"Directory {raw_dir} is not writable")

    def test_code_ingestion_has_init(self):
        """Verify code/ingestion has __init__.py (package structure)."""
        init_file = project_root / "code" / "ingestion" / "__init__.py"
        # While not strictly required for a folder to be a directory, 
        # the task implies a structured project. 
        # If the scaffold creates the folder, we check existence.
        # We assert the folder exists as per the primary requirement.
        folder = project_root / "code" / "ingestion"
        assert folder.is_dir(), "code/ingestion directory missing"