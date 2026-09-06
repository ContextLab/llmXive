import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Verify that the required project directory structure exists.
    This test runs after T001 implementation.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    required_dirs = [
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        "data/raw",
        "data/simulated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "docs/paper",
    ]
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_gitkeep_files_exist():
    """
    Verify that .gitkeep files exist in data directories.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dirs = ["data/raw", "data/simulated", "data/results"]
    
    for dir_path in data_dirs:
        full_path = base_dir / dir_path
        gitkeep = full_path / ".gitkeep"
        assert gitkeep.exists(), f".gitkeep missing in: {full_path}"

def test_tree_manifest_exists():
    """
    Verify that tree_manifest.txt was created in the project root.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    manifest_path = base_dir / "tree_manifest.txt"
    assert manifest_path.exists(), "tree_manifest.txt not found in project root"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify it contains expected directory names
    assert "code/simulation" in content or "simulation" in content, "Manifest missing code/simulation reference"
    assert "data/raw" in content or "raw" in content, "Manifest missing data/raw reference"
    assert "tests/unit" in content or "unit" in content, "Manifest missing tests/unit reference"