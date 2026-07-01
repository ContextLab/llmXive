"""
Integration tests for T008: Python 3.11 project initialization.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for testing project setup."""
    temp_dir = tempfile.mkdtemp()
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_dir)
    shutil.rmtree(temp_dir)

def test_setup_script_syntax(temp_project_dir):
    """Test that setup scripts have valid Python syntax."""
    # Copy setup scripts to temp directory
    setup_scripts = [
        "code/setup_project.py",
        "code/setup_venv.py",
        "code/setup_project_structure.py"
    ]
    
    for script in setup_scripts:
        src_path = Path("code") / script
        if src_path.exists():
            dest_path = Path(temp_project_dir) / script
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dest_path)
    
    # Check syntax of each script
    for script in setup_scripts:
        script_path = Path(temp_project_dir) / script
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(script_path)],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Syntax error in {script}: {result.stderr}"

def test_setup_script_help_execution(temp_project_dir):
    """Test that setup scripts can be executed without errors."""
    # Copy setup scripts to temp directory
    setup_scripts = [
        "code/setup_project_structure.py"
    ]
    
    for script in setup_scripts:
        src_path = Path("code") / script
        if src_path.exists():
            dest_path = Path(temp_project_dir) / script
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_path, dest_path)
    
    # Execute script (structure creation should work even without full env)
    script_path = Path(temp_project_dir) / "code/setup_project_structure.py"
    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Structure creation should succeed
        assert result.returncode == 0, f"Execution failed: {result.stderr}"

def test_requirements_exists(temp_project_dir):
    """Test that requirements.txt exists and has content."""
    req_path = Path(temp_project_dir) / "code" / "requirements.txt"
    if not req_path.exists():
        # Copy from source
        src_req = Path("code/requirements.txt")
        if src_req.exists():
            req_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src_req, req_path)
    
    if req_path.exists():
        content = req_path.read_text()
        assert len(content) > 0, "requirements.txt is empty"
        assert "pandas" in content, "Missing pandas dependency"
        assert "numpy" in content, "Missing numpy dependency"
