"""
Test suite for project setup and directory structure.
"""
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_directories_exist():
    """Verify that required directories exist."""
    required_dirs = [
        'data', 'data/raw', 'data/processed', 'data/models', 'data/logs',
        'code', 'tests', 'docs', 'contracts'
    ]
    for dir_name in required_dirs:
        path = os.path.join(PROJECT_ROOT, dir_name)
        assert os.path.isdir(path), f"Directory {path} does not exist."

def test_files_exist():
    """Verify that required files exist."""
    required_files = [
        'README.md', '.gitignore', 'requirements.txt',
        'contracts/dataset.schema.yaml', 'contracts/model_output.schema.yaml'
    ]
    for file_name in required_files:
        path = os.path.join(PROJECT_ROOT, file_name)
        assert os.path.isfile(path), f"File {path} does not exist."