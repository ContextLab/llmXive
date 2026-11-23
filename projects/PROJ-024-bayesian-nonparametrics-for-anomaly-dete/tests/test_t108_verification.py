"""
Unit test for T108: Source Relocation Verification.
Verifies that no .py files exist at the code/ root level.
"""
import os
import subprocess
from pathlib import Path
import pytest

def test_no_py_files_at_code_root():
    """
    Verify that code/ root contains no .py files.
    This is the primary constraint for T108.
    """
    project_root = Path(__file__).parent.parent / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    code_root = project_root / "code"
    
    # Find all .py files at code/ root (maxdepth 1)
    py_files = list(code_root.glob("*.py"))
    
    # Filter out __init__.py if it exists at root (though it shouldn't)
    actual_files = [f for f in py_files if f.name != "__init__.py"]
    
    assert len(actual_files) == 0, (
        f"Found {len(actual_files)} .py files at code/ root level: "
        f"{[f.name for f in actual_files]}. "
        "All source files must be under code/src/."
    )

def test_no_unexpected_dirs_at_code_root():
    """
    Verify that code/ root contains only expected directories.
    """
    project_root = Path(__file__).parent.parent / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    code_root = project_root / "code"
    
    expected_dirs = {"src", "tests", "scripts", "__pycache__"}
    
    # Get all directories at code/ root
    actual_dirs = {d.name for d in code_root.iterdir() if d.is_dir()}
    
    unexpected = actual_dirs - expected_dirs
    # Ignore __pycache__ and hidden dirs
    unexpected = {d for d in unexpected if not d.startswith('__') and d != '__pycache__'}
    
    assert len(unexpected) == 0, (
        f"Found unexpected directories at code/ root: {unexpected}. "
        f"Expected only: {expected_dirs}"
    )

def test_verification_script_runs_successfully():
    """
    Test that the verification script runs and exits with code 0.
    """
    project_root = Path(__file__).parent.parent / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
    script_path = project_root / "code" / "scripts" / "verify_source_relocation.py"
    
    if not script_path.exists():
        pytest.skip("Verification script not found")
    
    result = subprocess.run(
        ["python", str(script_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, (
        f"Verification script failed with code {result.returncode}\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )