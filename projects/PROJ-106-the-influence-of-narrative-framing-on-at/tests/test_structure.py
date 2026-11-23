"""
Unit tests to verify the project directory structure exists.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def root_dir():
    return Path(".")

def test_code_directory_exists(root_dir):
    assert (root_dir / "code").exists(), "code/ directory must exist"
    assert (root_dir / "code" / "utils").exists(), "code/utils/ directory must exist"

def test_data_directories_exist(root_dir):
    assert (root_dir / "data").exists(), "data/ directory must exist"
    assert (root_dir / "data" / "raw").exists(), "data/raw/ directory must exist"
    assert (root_dir / "data" / "processed").exists(), "data/processed/ directory must exist"
    assert (root_dir / "data" / "stimuli").exists(), "data/stimuli/ directory must exist"
    assert (root_dir / "data" / "ethics").exists(), "data/ethics/ directory must exist"

def test_tests_directory_exists(root_dir):
    assert (root_dir / "tests").exists(), "tests/ directory must exist"

def test_specs_directory_exists(root_dir):
    assert (root_dir / "specs").exists(), "specs/ directory must exist"