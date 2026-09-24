"""Test that code skeleton files exist."""
import os
import pytest

def test_skeleton_files_exist():
    """Assert that all listed files in code/ exist."""
    required_files = [
        "code/config.yaml",
        "code/download.py",
        "code/preprocess.py",
        "code/features.py",
        "code/analysis.py",
        "code/report.py",
        "code/models/__init__.py",
    ]

    missing = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing.append(file_path)

    if missing:
        pytest.fail(f"Missing skeleton files: {missing}")