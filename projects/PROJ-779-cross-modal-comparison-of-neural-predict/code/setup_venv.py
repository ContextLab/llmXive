"""
Virtual environment setup script for the project.

This script creates a `.venv` directory in the project root (if it does not already exist)
and installs all dependencies listed in `requirements.txt` using the pinned versions.
After successful installation, it records the output of `pip list` to a verification
file under `data/venv_setup_done.txt`.

The script is intended to be run as:
    python code/setup_venv.py

It exits with a non‑zero status if any step fails, ensuring the pipeline can detect
problems during the verification stage.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def run_command(command, env=None, check=True):
    """Run a shell command and return stdout (as text)."""
    log.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        check=False,
    )
    log.debug(f"Command output:\\n{result.stdout}")
    if check and result.returncode != 0:
        log.error(f"Command failed with exit code {result.returncode}")
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout
        )
    return result.stdout

def create_venv(venv_path: Path):
    """Create a virtual environment at the given path."""
    if venv_path.exists():
        log.info(f"Virtual environment already exists at {venv_path}")
    else:
        log.info(f"Creating virtual environment at {venv_path}")
        run_command([sys.executable, "-m", "venv", str(venv_path)])

def install_requirements(venv_path: Path, requirements_file: Path):
    """Install packages from requirements.txt into the virtual environment."""
    pip_executable = venv_path / "bin" / "pip"
    if not pip_executable.exists():
        # Windows compatibility
        pip_executable = venv_path / "Scripts" / "pip.exe"
    if not pip_executable.exists():
        raise FileNotFoundError(f"pip executable not found in virtual environment at {venv_path}")

    log.info(f"Installing dependencies from {requirements_file}")
    run_command([str(pip_executable), "install", "--upgrade", "pip"])
    run_command([str(pip_executable), "install", "-r", str(requirements_file)])

def capture_pip_list(venv_path: Path) -> str:
    """Capture the output of `pip list` from the virtual environment."""
    pip_executable = venv_path / "bin" / "pip"
    if not pip_executable.exists():
        pip_executable = venv_path / "Scripts" / "pip.exe"
    output = run_command([str(pip_executable), "list"])
    return output

def main():
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.is_file():
        log.error(f"requirements.txt not found at {requirements_path}")
        sys.exit(1)

    try:
        create_venv(venv_path)
        install_requirements(venv_path, requirements_path)
        pip_list_output = capture_pip_list(venv_path)

        # Write verification file
        verification_path = paths.data("venv_setup_done.txt")
        verification_path.parent.mkdir(parents=True, exist_ok=True)
        verification_path.write_text(pip_list_output, encoding="utf-8")
        log.info(f"Virtual environment setup complete. pip list written to {verification_path}")

    except Exception as e:
        log.exception("Virtual environment setup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()