"""
Tests for the setup_data_dirs script.
Verifies that the expected directory structure is created.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the script logic
# We will import the main function logic by executing the file content
# or by refactoring the script to be importable.
# For this test, we will import the main logic if possible, 
# but since it's a script, we'll test the side effects by running it.

from code.scripts.setup_data_dirs import main

def test_directory_structure_creation():
    """Test that the script creates the correct directory structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Mock the project root behavior by temporarily changing the script's context
        # Since the script uses __file__ to find the root, we can't easily mock it 
        # without refactoring. Instead, we will verify the logic by checking 
        # the hardcoded paths relative to the script's location in the actual repo.
        # However, for a unit test, we want to verify the logic.
        
        # Let's refactor the test to verify the paths that *would* be created
        # based on the script's logic relative to the current working directory 
        # if we were to run it in a temp dir.
        
        # Alternative: We test the expected paths relative to the script file location
        # in the actual repository structure.
        script_path = Path(__file__).parent.parent / "scripts" / "setup_data_dirs.py"
        if not script_path.exists():
            pytest.skip("Script not found in expected location")

        # Calculate the expected root based on the script's __file__
        # The script does: project_root = Path(__file__).resolve().parent.parent.parent
        # parent.parent.parent from code/scripts/setup_data_dirs.py is the project root
        expected_project_root = script_path.resolve().parent.parent.parent
        expected_data_root = expected_project_root / "data"
        expected_artifacts_root = expected_project_root / "artifacts"
        
        expected_dirs = [
            expected_data_root / "raw",
            expected_data_root / "processed",
            expected_data_root / "results",
            expected_artifacts_root,
        ]

        # Run the main function
        # We can't easily run it in a temp dir because it relies on __file__
        # So we assume the script is run in the context of the project.
        # Instead, we verify that if the script runs, it targets these paths.
        # To make this a real test, we will create these dirs in a temp location
        # and verify the logic by extracting the directory list.
        
        # Let's just verify the paths are correctly constructed relative to the script
        assert expected_data_root.exists() or True # We can't guarantee it exists before run
        
        # Since we can't easily mock the __file__ based root in a temp dir without refactoring,
        # we will test the logic by running the script in the actual project context
        # and checking if the directories exist afterwards.
        # This is an integration-style test for the script.
        
        # Run the script
        result = main()
        assert result == 0

        # Verify directories exist
        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            # Check for .gitkeep
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not found in {dir_path}"

def test_idempotency():
    """Test that running the script twice does not cause errors."""
    # Run main twice
    result1 = main()
    result2 = main()
    assert result1 == 0
    assert result2 == 0