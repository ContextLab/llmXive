"""
Unit test to verify that the create_logs_dir script creates the logs directory.
"""

import os
from pathlib import Path

def test_create_logs_dir():
    # Import the script's main function
    from code.create_logs_dir import main as create_logs_main
    
    # Ensure logs directory is removed if it exists to test creation
    root = Path(__file__).resolve().parents[3]  # project root
    logs_path = root / "logs"
    if logs_path.exists():
        # Remove directory recursively for a clean test
        for child in logs_path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                # Remove subdirectories if any (unlikely)
                import shutil
                shutil.rmtree(child)
        logs_path.rmdir()
    
    # Run the creation script
    create_logs_main()
    
    # Assert the directory now exists
    assert logs_path.is_dir(), "logs directory was not created by create_logs_dir script"

# The test can be run via `pytest -q tests/unit/test_create_logs_dir.py` and should pass.