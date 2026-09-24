import os
import pytest
from pathlib import Path

def test_code_src_directory_exists():
    """Verify that code/src/ directory exists."""
    root = Path(__file__).resolve().parent.parent
    code_src = root / "code" / "src"
    assert code_src.exists(), f"Directory {code_src} does not exist"
    assert code_src.is_dir(), f"{code_src} is not a directory"

def test_code_tests_directory_exists():
    """Verify that code/tests/ directory exists."""
    root = Path(__file__).resolve().parent.parent
    code_tests = root / "code" / "tests"
    assert code_tests.exists(), f"Directory {code_tests} does not exist"
    assert code_tests.is_dir(), f"{code_tests} is not a directory"

def test_src_init_exists():
    """Verify that code/src/__init__.py exists."""
    root = Path(__file__).resolve().parent.parent
    init_file = root / "code" / "src" / "__init__.py"
    assert init_file.exists(), f"File {init_file} does not exist"

def test_tests_init_exists():
    """Verify that code/tests/__init__.py exists."""
    root = Path(__file__).resolve().parent.parent
    init_file = root / "code" / "tests" / "__init__.py"
    assert init_file.exists(), f"File {init_file} does not exist"