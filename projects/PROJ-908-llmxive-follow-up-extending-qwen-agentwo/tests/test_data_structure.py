"""
Test to verify the data directory structure and .gitignore configuration.
This satisfies T006 requirements.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GITIGNORE_PATH = DATA_DIR / ".gitignore"

def test_data_directory_exists():
    """Verify the main data directory exists."""
    assert DATA_DIR.exists(), f"Directory {DATA_DIR} does not exist."
    assert DATA_DIR.is_dir(), f"{DATA_DIR} is not a directory."

def test_raw_directory_exists():
    """Verify the data/raw directory exists."""
    assert RAW_DIR.exists(), f"Directory {RAW_DIR} does not exist."
    assert RAW_DIR.is_dir(), f"{RAW_DIR} is not a directory."

def test_processed_directory_exists():
    """Verify the data/processed directory exists."""
    assert PROCESSED_DIR.exists(), f"Directory {PROCESSED_DIR} does not exist."
    assert PROCESSED_DIR.is_dir(), f"{PROCESSED_DIR} is not a directory."

def test_gitkeep_files_exist():
    """Verify .gitkeep files exist to preserve directory structure in git."""
    assert (RAW_DIR / ".gitkeep").exists(), f"{RAW_DIR}/.gitkeep missing."
    assert (PROCESSED_DIR / ".gitkeep").exists(), f"{PROCESSED_DIR}/.gitkeep missing."

def test_readme_files_exist():
    """Verify README.md files exist in data directories."""
    assert (RAW_DIR / "README.md").exists(), f"{RAW_DIR}/README.md missing."
    assert (PROCESSED_DIR / "README.md").exists(), f"{PROCESSED_DIR}/README.md missing."

def test_gitignore_exists():
    """Verify .gitignore exists in the data directory."""
    assert GITIGNORE_PATH.exists(), f"{GITIGNORE_PATH} does not exist."

def test_gitignore_content():
    """Verify .gitignore contains expected ignore patterns."""
    content = GITIGNORE_PATH.read_text()
    assert "*" in content, ".gitignore should ignore all files by default."
    assert "!raw/.gitkeep" in content, ".gitignore should preserve raw/.gitkeep."
    assert "!processed/.gitkeep" in content, ".gitignore should preserve processed/.gitkeep."