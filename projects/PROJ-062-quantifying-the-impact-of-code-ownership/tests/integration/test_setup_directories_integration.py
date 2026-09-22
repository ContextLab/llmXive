import os
import pytest
from pathlib import Path
import tempfile
import shutil
import subprocess

def test_setup_directories_integration():
    """
    Integration test to verify that the setup_directories script creates the required
    directory structure and .gitkeep files in the project root.
    """
    # The script is expected to run from the project root or code/scripts directory.
    # We will run the script and verify the output.
    
    project_root = Path(__file__).parent.parent.parent
    script_path = project_root / "code" / "scripts" / "setup_directories.py"
    
    # Ensure the script exists
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Run the script
    result = subprocess.run(
        ["python", str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Check for successful execution
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Verify directories exist
    data_raw = project_root / "data" / "raw"
    data_intermediate = project_root / "data" / "intermediate"
    data_results = project_root / "data" / "results"
    
    assert data_raw.exists(), f"Directory {data_raw} was not created"
    assert data_intermediate.exists(), f"Directory {data_intermediate} was not created"
    assert data_results.exists(), f"Directory {data_results} was not created"
    
    # Verify .gitkeep files exist
    gitkeep_raw = data_raw / ".gitkeep"
    gitkeep_intermediate = data_intermediate / ".gitkeep"
    gitkeep_results = data_results / ".gitkeep"
    
    assert gitkeep_raw.exists(), f".gitkeep file not found in {data_raw}"
    assert gitkeep_intermediate.exists(), f".gitkeep file not found in {data_intermediate}"
    assert gitkeep_results.exists(), f".gitkeep file not found in {data_results}"