"""
Tests for T002 project initialization.
"""
import os
import subprocess
from pathlib import Path

def test_requirements_exists():
    """Verify requirements.txt exists and contains expected dependencies."""
    project_root = Path(__file__).parent.parent
    req_path = project_root / "requirements.txt"
    
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text()
    required = ["numpy", "pandas", "nilearn", "networkx", "scikit-learn", 
                "statsmodels", "pingouin", "datasets", "pytest", "jsonschema"]
    
    for dep in required:
        assert any(dep in line for line in content.splitlines()), f"Missing dependency: {dep}"

def test_setup_script_runs():
    """Verify the setup script runs without error."""
    project_root = Path(__file__).parent.parent
    setup_script = project_root / "setup_project.py"
    
    assert setup_script.exists(), "setup_project.py not found"
    
    result = subprocess.run(
        ["python", str(setup_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    assert "Project initialization complete" in result.stdout