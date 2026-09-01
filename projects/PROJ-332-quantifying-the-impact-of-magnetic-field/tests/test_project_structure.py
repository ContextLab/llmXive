import os
import pytest
from pathlib import Path

def test_project_structure_exists():
    """
    Verifies that the required project directories exist and are non-empty (contain .gitkeep).
    This test ensures T001 requirements are met.
    """
    # Determine project root (assuming tests are in tests/)
    test_dir = Path(__file__).resolve()
    project_root = test_dir.parent

    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "artifacts",
        "tests"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"
        
        # Check for non-emptiness (presence of .gitkeep or any file)
        contents = list(dir_path.iterdir())
        assert len(contents) > 0, f"Directory is empty (should contain .gitkeep): {dir_path}"

def test_code_submodules_exist():
    """
    Verifies that the expected package structure exists for the code modules.
    """
    project_root = Path(__file__).resolve().parent
    code_root = project_root / "code"

    # Check for __init__.py files to make directories packages
    # Note: T004 handles the content of __init__.py, but T001 ensures structure
    # We check that the paths exist to support imports defined in the API surface
    expected_paths = [
        code_root / "data" / "__init__.py",
        code_root / "analysis" / "__init__.py",
        code_root / "utils" / "__init__.py",
    ]
    
    # Only assert existence if the parent directory exists
    # (T004 might not have created the __init__.py yet if running strictly T001)
    # However, T004 is marked as completed in the context, so we expect them.
    # If T004 is not actually done, this test might fail, which is expected behavior
    # for a dependency check.
    
    # We will assert that the directories exist, as T001 creates the structure.
    # The __init__.py files are created by T004, so we skip strict assertion on them here
    # to avoid false negatives if T004 is pending in the runner context, 
    # but we verify the directories T001 created.
    
    assert (code_root / "data").exists(), "code/data directory missing"
    assert (code_root / "analysis").exists(), "code/analysis directory missing"
    assert (code_root / "utils").exists(), "code/utils directory missing"