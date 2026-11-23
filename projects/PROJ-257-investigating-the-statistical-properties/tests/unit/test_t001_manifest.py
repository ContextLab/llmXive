"""
Unit tests for T001: Project Structure Initialization and Manifest.

Verifies that the directory structure was created correctly
and the manifest file contains the expected data.
"""
import json
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "project_structure_manifest.json"

REQUIRED_TOP_LEVEL_DIRS = {"src", "tests", "data", "output", "logs"}

@pytest.fixture
def manifest_data():
    """Load the manifest file for testing."""
    if not MANIFEST_PATH.exists():
        pytest.fail(f"Manifest file not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_manifest_exists():
    """Test that the manifest file exists."""
    assert MANIFEST_PATH.exists(), "project_structure_manifest.json must exist"

def test_manifest_is_valid_json(manifest_data):
    """Test that the manifest is valid JSON (already handled by fixture, but explicit check)."""
    assert isinstance(manifest_data, dict), "Manifest root must be a dictionary"

def test_required_top_level_dirs_present(manifest_data):
    """Test that all required top-level directories are in the manifest."""
    keys = set(manifest_data.keys())
    missing = REQUIRED_TOP_LEVEL_DIRS - keys
    assert not missing, f"Missing required top-level directories in manifest: {missing}"

def test_data_subdirs_present(manifest_data):
    """Test that 'data' contains required subdirectories."""
    data_dirs = set(manifest_data.get("data", []))
    required_data_subdirs = {"raw", "processed"}
    missing = required_data_subdirs - data_dirs
    assert not missing, f"Missing required subdirectories under 'data': {missing}"

def test_src_subdirs_present(manifest_data):
    """Test that 'src' contains required subdirectories."""
    src_dirs = set(manifest_data.get("src", []))
    required_src_subdirs = {"data", "analysis", "viz", "utils"}
    missing = required_src_subdirs - src_dirs
    assert not missing, f"Missing required subdirectories under 'src': {missing}"

def test_tests_subdirs_present(manifest_data):
    """Test that 'tests' contains required subdirectories."""
    tests_dirs = set(manifest_data.get("tests", []))
    required_tests_subdirs = {"unit", "integration", "contract"}
    missing = required_tests_subdirs - tests_dirs
    assert not missing, f"Missing required subdirectories under 'tests': {missing}"

def test_output_subdirs_present(manifest_data):
    """Test that 'output' contains required subdirectories."""
    output_dirs = set(manifest_data.get("output", []))
    required_output_subdirs = {"results", "figures"}
    missing = required_output_subdirs - output_dirs
    assert not missing, f"Missing required subdirectories under 'output': {missing}"

def test_actual_directories_exist(manifest_data):
    """Verify that the directories listed in the manifest actually exist on disk."""
    for top_dir, subdirs in manifest_data.items():
        top_path = PROJECT_ROOT / top_dir
        assert top_path.exists(), f"Top-level directory {top_dir} does not exist"
        
        for subdir in subdirs:
            subdir_path = top_path / subdir
            assert subdir_path.exists(), f"Subdirectory {top_dir}/{subdir} does not exist"
            assert subdir_path.is_dir(), f"{top_dir}/{subdir} is not a directory"