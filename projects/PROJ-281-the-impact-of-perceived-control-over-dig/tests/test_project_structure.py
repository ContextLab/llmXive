"""
Integration test to verify project structure creation (Task T001).
"""
import os
import pathlib
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "specs",
]

REQUIRED_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
    "data/__init__.py",
    "specs/__init__.py",
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
]

def test_directories_exist():
    """Verify all required directories exist."""
    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Not a directory: {dir_path}"

def test_files_exist():
    """Verify all required files exist."""
    for file_name in REQUIRED_FILES:
        file_path = PROJECT_ROOT / file_name
        assert file_path.exists(), f"File missing: {file_path}"
        assert file_path.is_file(), f"Not a file: {file_path}"

def test_init_files_are_valid():
    """Verify __init__.py files are non-empty and importable."""
    init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "data/__init__.py",
        "specs/__init__.py",
    ]
    for init_file in init_files:
        file_path = PROJECT_ROOT / init_file
        assert file_path.stat().st_size > 0, f"Empty __init__.py: {file_path}"

        # Verify it's valid Python by attempting import (mocked context)
        # We check syntax only here to avoid complex path manipulation in test
        import ast
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                ast.parse(f.read())
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}: {e}")