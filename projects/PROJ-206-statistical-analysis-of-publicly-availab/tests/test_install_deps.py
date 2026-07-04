import os
import sys
import subprocess
from pathlib import Path

def test_requirements_file_exists():
    """Verify requirements.txt exists at project root."""
    root = Path(__file__).resolve().parent.parent
    req_file = root / "requirements.txt"
    assert req_file.exists(), "requirements.txt must exist at project root"

def test_virtual_env_created():
    """Verify the virtual environment directory exists."""
    root = Path(__file__).resolve().parent.parent
    venv_dir = root / "venv"
    assert venv_dir.exists(), "venv/ directory must exist after running install_deps.py"
    
    # Check for pip executable to ensure it's a valid venv
    if os.name == 'nt':
        pip_path = venv_dir / "Scripts" / "pip"
    else:
        pip_path = venv_dir / "bin" / "pip"
    
    assert pip_path.exists(), f"pip executable not found in {venv_dir}"

def test_pandas_installed():
    """Verify a core dependency (pandas) is installed in the venv."""
    root = Path(__file__).resolve().parent.parent
    if os.name == 'nt':
        python_path = root / "venv" / "Scripts" / "python"
    else:
        python_path = root / "venv" / "bin" / "python"
    
    assert python_path.exists(), "venv python executable not found"
    
    result = subprocess.run(
        [str(python_path), "-c", "import pandas; print(pandas.__version__)"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"pandas not installed in venv: {result.stderr}"