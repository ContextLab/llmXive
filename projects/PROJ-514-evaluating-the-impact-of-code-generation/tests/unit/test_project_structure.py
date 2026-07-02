"""
Unit tests to verify the project directory structure was created correctly.
These tests validate that T001 successfully created the required folders.
"""
import os
import pytest

# The expected directories relative to the project root
EXPECTED_DIRS = [
    "code/01_data_collection",
    "code/02_static_analysis",
    "code/03_statistical_analysis",
    "code/04_reporting",
    "code/utils",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "data/raw/human_samples",
    "data/raw/llm_samples",
    "data/intermediate",
    "data/processed",
    "reports",
    "specs/001-code-smell-comparison"
]

def get_project_root():
    """Determine the project root (assuming tests are in tests/unit)"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@pytest.fixture(scope="module")
def root_path():
    return get_project_root()

@pytest.mark.parametrize("dir_rel_path", EXPECTED_DIRS)
def test_directory_exists(root_path, dir_rel_path):
    """Assert that each required directory exists on disk."""
    full_path = os.path.join(root_path, dir_rel_path)
    assert os.path.isdir(full_path), f"Directory missing: {full_path}"

def test_code_structure_integrity(root_path):
    """Verify the main code hierarchy exists."""
    code_root = os.path.join(root_path, "code")
    assert os.path.isdir(code_root), "Root 'code' directory missing"
    
    subdirs = ["01_data_collection", "02_static_analysis", "03_statistical_analysis", "04_reporting", "utils"]
    for subdir in subdirs:
        assert os.path.isdir(os.path.join(code_root, subdir)), f"Missing code subdir: {subdir}"

def test_data_structure_integrity(root_path):
    """Verify the main data hierarchy exists."""
    data_root = os.path.join(root_path, "data")
    assert os.path.isdir(data_root), "Root 'data' directory missing"
    
    subdirs = ["intermediate", "processed"]
    raw_subdirs = ["human_samples", "llm_samples"]
    
    for subdir in subdirs:
        assert os.path.isdir(os.path.join(data_root, subdir)), f"Missing data subdir: {subdir}"
        
    raw_root = os.path.join(data_root, "raw")
    assert os.path.isdir(raw_root), "Missing 'data/raw' directory"
    for subdir in raw_subdirs:
        assert os.path.isdir(os.path.join(raw_root, subdir)), f"Missing data/raw subdir: {subdir}"
