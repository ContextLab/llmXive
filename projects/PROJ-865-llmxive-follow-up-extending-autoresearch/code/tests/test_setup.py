"""
Basic sanity test for directory creation scripts.
Verifies that T001l (code/tests/) and other setup tasks created expected directories.
"""
import os
import sys
from pathlib import Path

import pytest

# Add project root to path to import setup modules if needed
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def test_code_tests_directory_exists():
    """Verify that code/tests/ directory exists (Task T001l)."""
    test_dir = project_root / "code" / "tests"
    assert test_dir.exists(), f"Directory does not exist: {test_dir}"
    assert test_dir.is_dir(), f"Not a directory: {test_dir}"

def test_code_tests_init_exists():
    """Verify that code/tests/__init__.py exists to make it a package."""
    init_file = project_root / "code" / "tests" / "__init__.py"
    assert init_file.exists(), f"__init__.py missing: {init_file}"

def test_code_directory_structure():
    """Verify basic code/ directory structure created by setup tasks."""
    expected_dirs = [
        "code/01_data_ingestion",
        "code/02_annotation_distillation",
        "code/03_execution",
        "code/04_analysis",
        "code/utils",
        "code/tests",
    ]
    for dir_path in expected_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Expected directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"