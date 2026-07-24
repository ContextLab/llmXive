import os
import sys
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directories

def test_directories_created(tmp_path):
    """
    Test that the required source directories are created.
    
    Verifies:
    - code/utils exists
    - code/data exists
    """
    # Create a temporary project root
    project_root = tmp_path / "projects" / "PROJ-096-exploring-the-role-of-network-topology-o"
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Run the function
    create_directories(project_root)
    
    # Assertions
    code_utils = project_root / "code" / "utils"
    code_data = project_root / "code" / "data"
    
    assert code_utils.exists(), f"Directory {code_utils} was not created"
    assert code_utils.is_dir(), f"{code_utils} is not a directory"
    
    assert code_data.exists(), f"Directory {code_data} was not created"
    assert code_data.is_dir(), f"{code_data} is not a directory"

def test_directories_idempotent(tmp_path):
    """
    Test that running the function twice does not cause errors.
    """
    project_root = tmp_path / "projects" / "PROJ-096-exploring-the-role-of-network-topology-o"
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Run twice
    create_directories(project_root)
    create_directories(project_root)
    
    # Assertions
    assert (project_root / "code" / "utils").exists()
    assert (project_root / "code" / "data").exists()