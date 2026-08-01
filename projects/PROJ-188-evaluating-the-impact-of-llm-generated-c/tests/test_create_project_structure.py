import os
import pytest
from pathlib import Path
from code.create_project_structure import create_project_structure

def test_create_project_structure():
    """
    Test that the project root directory is created successfully.
    """
    # Clean up if it exists from previous runs
    target_path = Path("projects/PROJ-188-evaluating-the-impact-of-llm-generated-c")
    if target_path.exists():
        # We don't remove it to avoid deleting user data if run manually,
        # but for the test we assume it's fresh or the function handles exist_ok=True
        pass
    
    result_path = create_project_structure()
    
    assert Path(result_path).exists(), f"Directory {result_path} was not created"
    assert Path(result_path).is_dir(), f"{result_path} is not a directory"