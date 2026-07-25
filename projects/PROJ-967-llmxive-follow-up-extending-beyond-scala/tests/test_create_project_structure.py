import os
import sys
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_project_structure import ensure_directory, main

def test_ensure_directory_creates_new():
    """Test that ensure_directory creates a new directory."""
    test_dir = Path("test_temp_new_dir")
    if test_dir.exists():
        test_dir.rmdir()
    
    ensure_directory(test_dir)
    assert test_dir.exists()
    assert test_dir.is_dir()
    
    # Cleanup
    test_dir.rmdir()

def test_ensure_directory_skips_existing():
    """Test that ensure_directory does not fail if directory exists."""
    test_dir = Path("test_temp_existing_dir")
    test_dir.mkdir(exist_ok=True)
    
    ensure_directory(test_dir)
    assert test_dir.exists()
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

def test_main_creates_structure():
    """Test that main creates the expected directory structure."""
    project_root = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
    
    # Clean up if it exists from previous runs to ensure a fresh test
    if project_root.exists():
        import shutil
        shutil.rmtree(project_root)
    
    main()
    
    expected_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results",
    ]
    
    for dir_path in expected_dirs:
        assert dir_path.exists(), f"Directory {dir_path} was not created by main()"
        assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory"
    
    # Cleanup
    import shutil
    shutil.rmtree(project_root)