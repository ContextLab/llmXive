import subprocess
import sys
from pathlib import Path

def test_requirements_pin():
    """Ensure each line in requirements.txt matches package==version."""
    req_path = Path("requirements.txt")
    assert req_path.is_file(), "requirements.txt not found"
    for line in req_path.read_text().splitlines():
        line = line.strip()
        # Skip empty lines or comments
        if not line or line.startswith("#"):
            continue
        assert "==" in line, f"Requirement line not pinned: {line}"
        pkg, ver = line.split("==", 1)
        assert pkg and ver, f"Invalid requirement format: {line}"

def test_pip_install():
    """Attempt to install requirements in a subprocess to catch syntax errors."""
    # Use a temporary virtual environment to avoid polluting the runner env
    import venv, shutil, os, json
    venv_dir = Path(".venv_test")
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
    venv.create(venv_dir, with_pip=True)
    python_exe = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
    # Upgrade pip
    subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
    # Install requirements
    subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"], stdout=subprocess.DEVNULL)
    # Clean up
    shutil.rmtree(venv_dir)