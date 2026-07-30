"""
Unit tests for the artifact directory creation script.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function from the sibling module
# Since the test is in tests/unit/, we need to adjust the path or use relative imports
# For simplicity in this isolated test, we will mock the path logic or import directly
# assuming the environment is set up correctly (sys.path includes project root)

import sys
from pathlib import Path

# Add the project root to the path if not already there
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.create_artifact_dirs import main

def test_artifact_dirs_created():
    """Test that the main function creates the required directories."""
    # We will run this in a temporary directory to avoid polluting the actual project
    # However, the script uses __file__ to determine paths, which is fixed.
    # To properly test this, we would need to refactor the script to accept a root path,
    # or test the side effects on the actual file system.
    # Given the constraint to implement T003, we assume the script runs correctly in the project context.
    # This test verifies that the directories exist after running main().
    
    # Note: Since main() uses absolute paths based on __file__, we cannot easily mock it
    # without modifying the source. We will assume the source is correct and just verify
    # the existence of the directories after a simulated run in the actual project structure.
    
    # For the purpose of this task, we assert that the directories exist in the project root
    # relative to where this test is run (assuming the project structure is correct).
    # In a real CI/CD, the test would run from the project root.
    
    # Let's assume the project root is the parent of 'code' and 'tests'
    current_dir = Path(__file__).resolve().parent
    tests_dir = current_dir.parent
    project_root = tests_dir.parent
    
    artifacts_dir = project_root / "artifacts"
    models_dir = artifacts_dir / "models"
    reports_dir = artifacts_dir / "reports"
    figures_dir = artifacts_dir / "figures"
    
    # Run the main function to ensure directories are created
    # We need to change the current working directory to the project root
    # or ensure the script runs with the correct __file__ resolution.
    # Since we can't easily change __file__, we rely on the script's logic.
    # The script uses Path(__file__).resolve().parent.parent which should point to project_root
    
    # Let's call main() and then check
    # Note: This might fail if run from a different directory, but in the test environment
    # it should be run from the project root or the path resolution should work.
    
    # To be safe, we'll just check if the directories exist after running main()
    # If they don't, the test will fail, indicating an issue with the script or environment.
    
    # We need to handle the case where the script might fail to create dirs due to permissions
    # but for this test, we assume it works.
    
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
    
    assert artifacts_dir.exists(), f"Directory {artifacts_dir} does not exist"
    assert models_dir.exists(), f"Directory {models_dir} does not exist"
    assert reports_dir.exists(), f"Directory {reports_dir} does not exist"
    assert figures_dir.exists(), f"Directory {figures_dir} does not exist"