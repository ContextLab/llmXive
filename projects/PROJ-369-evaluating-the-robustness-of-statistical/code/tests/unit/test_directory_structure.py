"""
Unit tests to verify the project directory structure exists as required by T001.
"""
import pytest
from pathlib import Path
import sys
import os

# Ensure src is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from src.utils.config import get_path

REQUIRED_DIRECTORIES = [
    "src",
    "src/data",
    "src/synthesis",
    "src/analysis",
    "src/viz",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data/raw",
    "data/processed",
    "data/results",
    "specs",
    "state"
]

class TestDirectoryStructure:
    """Test cases for T001 - Project Directory Structure."""

    def test_required_directories_exist(self):
        """Verify all required directories from T001 exist."""
        root = get_path("")
        missing = []

        for dir_name in REQUIRED_DIRECTORIES:
            dir_path = root / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                missing.append(dir_name)

        assert len(missing) == 0, f"Missing required directories: {missing}"

    def test_directory_setup_script_exists(self):
        """Verify the setup script exists."""
        root = get_path("")
        setup_script = root / "scripts" / "setup_project_structure.py"
        assert setup_script.exists(), f"Setup script missing: {setup_script}"

    def test_verify_script_exists(self):
        """Verify the verification script exists."""
        root = get_path("")
        verify_script = root / "scripts" / "verify_project_structure.py"
        assert verify_script.exists(), f"Verification script missing: {verify_script}"

    def test_data_raw_directory_exists(self):
        """Specific check for data/raw as it's critical for ingestion."""
        root = get_path("")
        data_raw = root / "data" / "raw"
        assert data_raw.exists() and data_raw.is_dir()

    def test_data_processed_directory_exists(self):
        """Specific check for data/processed as it's critical for metrics."""
        root = get_path("")
        data_processed = root / "data" / "processed"
        assert data_processed.exists() and data_processed.is_dir()

    def test_src_modules_exist(self):
        """Verify core src modules directories exist."""
        root = get_path("")
        modules = ["data", "synthesis", "analysis", "viz", "utils"]
        for mod in modules:
            mod_path = root / "src" / mod
            assert mod_path.exists() and mod_path.is_dir(), f"Module directory missing: {mod_path}"