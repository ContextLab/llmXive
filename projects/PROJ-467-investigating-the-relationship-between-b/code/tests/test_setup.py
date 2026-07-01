import os
import subprocess
from pathlib import Path

def test_requirements_exists():
    """Verify that requirements.txt is present in the code directory."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "code" / "requirements.txt"
    assert req_file.exists(), "requirements.txt must exist in code/"
    
    # Verify content contains expected packages
    with open(req_file) as f:
        content = f.read()
    
    expected_packages = [
        "numpy", "pandas", "nilearn", "networkx", 
        "scikit-learn", "statsmodels", "pingouin", 
        "datasets", "pytest", "jsonschema"
    ]
    
    for pkg in expected_packages:
        assert pkg.lower() in content.lower(), f"Missing package: {pkg}"

def test_setup_script_runs():
    """Verify the setup script runs without error."""
    project_root = Path(__file__).parent.parent.parent
    script = project_root / "code" / "setup_project.py"
    
    # Run the script
    result = subprocess.run(
        ["python", str(script)],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    
    # Verify directories were created
    expected_dirs = [
        "code", "tests", "data/raw", "data/processed", 
        "results/figures", "metadata", "contracts", "specs"
    ]
    
    for d in expected_dirs:
        assert (project_root / d).exists(), f"Directory {d} should exist"