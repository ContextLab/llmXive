import os
import json
import pytest
from pathlib import Path
import sys

# Add code to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project import main

@pytest.fixture
def clean_env(tmp_path):
    """Create a temporary directory to act as project root."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_creates_directories(clean_env):
    """Test that main() creates all required directories."""
    # Run the setup
    exit_code = main()
    
    assert exit_code == 0, "Setup should exit with code 0 on success"

    required_dirs = [
        "code", "data", "tests", "state", "models",
        "data/raw", "data/processed", "reports"
    ]

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Directory {dir_name} should exist"
        assert dir_path.is_dir(), f"{dir_name} should be a directory"

def test_creates_manifest(clean_env):
    """Test that main() creates state/structure_manifest.json."""
    exit_code = main()
    assert exit_code == 0

    manifest_path = Path("state/structure_manifest.json")
    assert manifest_path.exists(), "Manifest file should exist"

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    assert "status" in manifest
    assert "directories" in manifest
    assert "verification" in manifest
    assert manifest["verification"]["all_exist"] is True
    assert len(manifest["directories"]["created"]) > 0