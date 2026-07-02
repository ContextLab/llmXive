"""
Contract tests to ensure the project structure adheres to architectural constraints.
"""
import os
import pytest

# Contract: Code directories must be writable
@pytest.mark.parametrize("dir_path", [
    "code/simulation",
    "code/gap_filling",
    "code/analysis",
    "code/pipeline"
])
def test_code_directories_writable(dir_path):
    """Verify code directories are writable."""
    assert os.access(dir_path, os.W_OK), f"Code directory not writable: {dir_path}"

# Contract: Data directories must be writable
@pytest.mark.parametrize("dir_path", [
    "data/raw",
    "data/derived",
    "data/metadata",
    "data/results"
])
def test_data_directories_writable(dir_path):
    """Verify data directories are writable."""
    assert os.access(dir_path, os.W_OK), f"Data directory not writable: {dir_path}"

# Contract: Test directories must be writable
@pytest.mark.parametrize("dir_path", [
    "tests/contract",
    "tests/unit",
    "tests/integration"
])
def test_test_directories_writable(dir_path):
    """Verify test directories are writable."""
    assert os.access(dir_path, os.W_OK), f"Test directory not writable: {dir_path}"

# Contract: No files should exist in root of newly created directories
def test_directories_are_empty():
    """Verify that created directories are empty (no files)."""
    for dir_path in [
        "code/simulation", "code/gap_filling", "code/analysis", "code/pipeline",
        "data/raw", "data/derived", "data/metadata", "data/results",
        "tests/contract", "tests/unit", "tests/integration"
    ]:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            assert len(files) == 0, f"Directory {dir_path} should be empty but contains: {files}"