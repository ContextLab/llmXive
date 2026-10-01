import os
import json
import pytest
from pathlib import Path
from setup_project import main

@pytest.fixture
def clean_env(tmp_path):
    """Change to a temporary directory to avoid polluting the real project root during tests."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_structure_creation(clean_env):
    """Verify that main() creates the required directories and manifest."""
    exit_code = main()
    assert exit_code == 0, "setup_project main() should return 0 on success"

    manifest_path = Path("state/structure_manifest.json")
    assert manifest_path.exists(), "Manifest file should be created"

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert manifest["status"] == "success"
    assert manifest["total_created"] > 0
    assert "code" in manifest["created_directories"][0] or any("code" in d for d in manifest["created_directories"])

    # Verify specific required directories exist on disk
    required_paths = [
        "code", "data", "tests", "state", "reports", "models",
        "data/raw", "data/processed"
    ]
    for p in required_paths:
        assert Path(p).is_dir(), f"Directory {p} should exist on disk"

def test_manifest_schema(clean_env):
    """Verify the manifest has the expected schema."""
    main()
    manifest_path = Path("state/structure_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert "status" in manifest
    assert "created_directories" in manifest
    assert "failed_directories" in manifest
    assert "total_created" in manifest
    assert "total_failed" in manifest