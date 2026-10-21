"""
Environment setup script for PROJ-345.
Creates a virtual environment in the project root (named '.venv')
and installs all pinned dependencies from the project's requirements.txt.
"""
import sys
import subprocess
import os
from pathlib import Path
import platform

def run_cmd(cmd, env=None):
    """Run a command and raise if it fails."""
    subprocess.check_call(cmd, env=env)

def get_venv_paths():
    """Return paths to the venv python and pip executables."""
    venv_dir = Path('.venv')
    if platform.system() == 'Windows':
        python_bin = venv_dir / 'Scripts' / 'python.exe'
        pip_bin = venv_dir / 'Scripts' / 'pip.exe'
    else:
        python_bin = venv_dir / 'bin' / 'python'
        pip_bin = venv_dir / 'bin' / 'pip'
    return python_bin, pip_bin

def create_venv():
    """Create a virtual environment in .venv if it does not already exist."""
    venv_dir = Path('.venv')
    if venv_dir.is_dir():
        print(f"Virtual environment already exists at {venv_dir.resolve()}")
        return
    print(f"Creating virtual environment at {venv_dir.resolve()}...")
    run_cmd([sys.executable, '-m', 'venv', str(venv_dir)])

def install_requirements(pip_path):
    """
    Install the pinned requirements using the venv's pip.
    The torch package requires the CPU‑only wheel index.
    """
    # Ensure we use the extra index for torch wheels
    env = os.environ.copy()
    # Preserve any existing extra-index-url and prepend the CPU torch URL
    extra_index = 'https://download.pytorch.org/whl/cpu'
    existing = env.get('PIP_EXTRA_INDEX_URL')
    if existing:
        env['PIP_EXTRA_INDEX_URL'] = f"{extra_index} {existing}"
    else:
        env['PIP_EXTRA_INDEX_URL'] = extra_index

    print("Installing dependencies from requirements.txt...")
    run_cmd([str(pip_path), 'install', '-r', 'requirements.txt'], env=env)

def main():
    create_venv()
    python_bin, pip_bin = get_venv_paths()
    if not pip_bin.is_file():
        print("Error: pip executable not found in the virtual environment.", file=sys.stderr)
        sys.exit(1)
    install_requirements(pip_bin)
    print("Environment setup complete. To activate the venv, run:")
    if platform.system() == 'Windows':
        print(r".\.venv\Scripts\activate")
    else:
        print(r"source .venv/bin/activate")

if __name__ == '__main__':
    main()