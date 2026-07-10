"""
Basic smoke test to verify project configuration and imports work.
"""
import pytest
from code.config import PROJECT_ROOT, DATA_RAW_DIR, DATA_PROCESSED_DIR

def test_project_root_exists():
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()

def test_data_dirs_exist():
    assert DATA_RAW_DIR.exists()
    assert DATA_PROCESSED_DIR.exists()
