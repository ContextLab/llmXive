import pathlib
import pytest
from pathlib import Path
import check_skeleton

@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent

def test_skeleton_directory_exists(project_root):
    missing = check_skeleton.missing_directories(project_root)
    assert len(missing) == 0, f"Missing directories in project root: {missing}"
