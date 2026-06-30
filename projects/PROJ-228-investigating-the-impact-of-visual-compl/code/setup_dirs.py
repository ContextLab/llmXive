import os
from pathlib import Path


def create_data_directories():
    """Create data directory structure: data/raw, data/interim, data/results."""
    base = Path("data")
    (base / "raw").mkdir(parents=True, exist_ok=True)
    (base / "interim").mkdir(parents=True, exist_ok=True)
    (base / "results").mkdir(parents=True, exist_ok=True)
    return base


def create_docs_directory():
    """Create documentation directory structure: docs."""
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    return docs_dir


def create_test_directories():
    """Create test directory structure: tests/unit, tests/integration."""
    base = Path("tests")
    (base / "unit").mkdir(parents=True, exist_ok=True)
    (base / "integration").mkdir(parents=True, exist_ok=True)
    return base


def create_source_directories():
    """Create source directory structure: code."""
    code_dir = Path("code")
    code_dir.mkdir(parents=True, exist_ok=True)
    return code_dir


def create_all_directories():
    """Create all required project directories."""
    create_source_directories()
    create_data_directories()
    create_test_directories()
    create_docs_directory()
    return True