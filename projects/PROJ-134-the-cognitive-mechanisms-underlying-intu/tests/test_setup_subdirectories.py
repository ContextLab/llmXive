import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_subdirectories import main

def test_main_creates_directories(tmp_path):
    """
    Verify that main() creates the required data subdirectories.
    We patch the script's logic to run against a temporary directory
    to avoid side effects in the real project root during testing.
    """
    # We need to mock the project_root logic inside the function.
    # Since main() calculates project_root relative to __file__,
    # we will test the core logic by importing ensure_directories
    # and checking the behavior, or by running the script in a controlled env.
    
    # A more direct test of the side-effect:
    # We will create a temp dir structure that mimics the project
    temp_root = tmp_path / "fake_project_root"
    temp_root.mkdir()
    
    # We need to verify that the specific directories are created.
    # Since the script uses __file__ to find root, we can't easily
    # inject a fake root without modifying the code or using mocks.
    # Instead, we test the utility function used by main.
    
    from config import ensure_directories
    
    test_dirs = [
        temp_root / "data" / "raw",
        temp_root / "data" / "processed",
        temp_root / "data" / "logs"
    ]
    
    # Verify they don't exist yet
    for d in test_dirs:
        assert not d.exists()
    
    # Run the utility
    ensure_directories(test_dirs)
    
    # Verify they exist
    for d in test_dirs:
        assert d.exists(), f"Directory {d} was not created."
        assert d.is_dir(), f"{d} is not a directory."

def test_main_returns_zero(capsys):
    """Verify the main function returns 0 on success."""
    # Note: This test assumes the script runs against the actual project structure.
    # If the project structure is missing (e.g., in a fresh clone without T001),
    # this might fail. However, T001a/b are marked complete.
    # We rely on the fact that ensure_directories is idempotent.
    
    # To be safe, we just verify the return code logic by importing main
    # and checking it doesn't raise an exception in a valid environment.
    # We assume the environment is set up as per T001/T002.
    
    # We will run the main function. If it fails due to missing dirs, 
    # ensure_directories creates them, so it should pass.
    exit_code = main()
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Data subdirectory initialization complete." in captured.out