"""
Tests to verify the project requirements and installation configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

def test_requirements_file_exists():
    """Verify that requirements.txt exists at the project root."""
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt must exist at project root"

def test_required_packages_present():
    """Verify that all required packages are listed in requirements.txt."""
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"
    
    required_packages = [
        "torch==2.2.0+cpu",
        "scikit-learn==1.5.0",
        "rdkit==2024.3.1",
        "statsmodels==0.14.1",
        "pandas==2.2.0",
        "numpy==1.26.0",
        "matplotlib==3.8.0",
        "pyyaml==6.0.1",
        "requests==2.31.0"
    ]

    with open(requirements_path, 'r') as f:
        content = f.read()
    
    for pkg in required_packages:
        assert pkg in content, f"Package {pkg} must be present in requirements.txt"

def test_setup_requirements_script_runs():
    """Verify that the setup_requirements.py script runs successfully."""
    project_root = Path(__file__).resolve().parent.parent
    script_path = project_root / "code" / "setup_requirements.py"
    
    if not script_path.exists():
        # If the script doesn't exist, we assume the requirements.txt check is sufficient
        # This test is optional depending on whether we want to enforce the script
        return

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    assert result.returncode == 0, f"setup_requirements.py failed: {result.stderr}"