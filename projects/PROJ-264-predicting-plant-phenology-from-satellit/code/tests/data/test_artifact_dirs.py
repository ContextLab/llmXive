import os
import pytest
from pathlib import Path
import sys

# Ensure the project root is in the path to import conftest helpers if needed,
# though we are testing file system state directly here.
project_root = Path(__file__).parent.parent.parent

def test_artifacts_directory_exists():
    """Verify that the artifacts/ directory exists."""
    artifacts_path = project_root / "artifacts"
    assert artifacts_path.exists(), f"Directory {artifacts_path} does not exist"
    assert artifacts_path.is_dir(), f"{artifacts_path} is not a directory"

def test_models_subdirectory_exists():
    """Verify that the artifacts/models/ subdirectory exists."""
    models_path = project_root / "artifacts" / "models"
    assert models_path.exists(), f"Directory {models_path} does not exist"
    assert models_path.is_dir(), f"{models_path} is not a directory"

def test_gitkeep_in_artifacts():
    """Verify that a .gitkeep file exists in artifacts/ to prevent deletion."""
    gitkeep_path = project_root / "artifacts" / ".gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file missing in {project_root / 'artifacts'}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

def test_gitkeep_in_models():
    """Verify that a .gitkeep file exists in artifacts/models/ to prevent deletion."""
    gitkeep_path = project_root / "artifacts" / "models" / ".gitkeep"
    assert gitkeep_path.exists(), f".gitkeep file missing in {project_root / 'artifacts' / 'models'}"
    assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"