"""
Test to verify that the required project directories exist.
"""
import os
import pytest

REQUIRED_DIRECTORIES = ["code", "data", "tests"]
REQUIRED_GITKEEP_FILES = [
    "code/.gitkeep",
    "data/.gitkeep",
    "tests/.gitkeep"
]

def test_required_directories_exist():
    """Verify that all required directories exist."""
    for directory in REQUIRED_DIRECTORIES:
        assert os.path.exists(directory), f"Directory '{directory}' does not exist."
        assert os.path.isdir(directory), f"'{directory}' is not a directory."

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in all required directories."""
    for file_path in REQUIRED_GITKEEP_FILES:
        assert os.path.exists(file_path), f"File '{file_path}' does not exist."
        assert os.path.isfile(file_path), f"'{file_path}' is not a file."

def test_gitkeep_files_are_non_empty_or_comment_only():
    """Verify that .gitkeep files contain at least a comment."""
    for file_path in REQUIRED_GITKEEP_FILES:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            # Allow empty files or files with just comments
            assert len(content) == 0 or content.startswith("#"), \
                f"File '{file_path}' should be empty or contain only comments."