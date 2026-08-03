import os
import pytest
import sys

# Add project root to path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import get_config, ensure_directories

@pytest.fixture
def config():
    return get_config()

def test_required_directories_exist(config):
    """
    Verify that the directories required by T001a and T001b exist.
    T001a: data/raw, data/processed, data/assets
    T001b: code, artifacts, tests
    """
    required_paths = [
        os.path.join(config.project_root, "data", "raw"),
        os.path.join(config.project_root, "data", "processed"),
        os.path.join(config.project_root, "data", "assets"),
        os.path.join(config.project_root, "code"),
        os.path.join(config.project_root, "artifacts"),
        os.path.join(config.project_root, "tests"),
    ]

    for path in required_paths:
        assert os.path.exists(path), f"Required directory does not exist: {path}"
        assert os.path.isdir(path), f"Path exists but is not a directory: {path}"

def test_ensure_directories_creates_missing(config, tmp_path):
    """Test that ensure_directories actually creates directories."""
    test_dir = os.path.join(tmp_path, "new_dir")
    assert not os.path.exists(test_dir)
    
    ensure_directories([test_dir])
    
    assert os.path.exists(test_dir)
    assert os.path.isdir(test_dir)