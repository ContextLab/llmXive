"""
Virtual environment setup script for the llmXive follow‑up project.

This script creates a Python ``venv`` in ``projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv/``,
installs the pinned requirements from the project's ``requirements.txt`` and writes a
verification log (Python version and ``pip list`` output) to ``venv/setup_log.txt``.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple

# Local utility imports
from utils.config import get_project_root, get_path, ensure_dirs_exist

def _venv_python_executable(venv_path: Path) -> Path:
    """
    Return the absolute path to the Python interpreter inside the virtual environment.
    Handles both POSIX (bin/python) and Windows (Scripts/python.exe) layouts.
    """
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def _venv_pip_executable(venv_path: Path) -> Path:
    """
    Return the absolute path to the ``pip`` executable inside the virtual environment.
    """
    if os.name == "nt":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def create_venv(venv_path: Path) -> bool:
    """
    Create a Python virtual environment at ``venv_path`` using ``python -m venv``.
    Returns ``True`` if creation succeeded, ``False`` otherwise.
    """
    try:
        # Ensure parent directories exist
        ensure_dirs_exist(venv_path.parent)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to create virtual environment: {e}", file=sys.stderr)
        return False

def install_dependencies(venv_path: Path, requirements_path: Path) -> Tuple[bool, str]:
    """
    Install the packages listed in ``requirements_path`` into the virtual environment.
    Returns a tuple ``(success, output)`` where ``output`` contains the combined
    stdout/stderr of the ``pip install`` command.
    """
    pip_exe = _venv_pip_executable(venv_path)
    try:
        result = subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stdout or e.stderr

def verify_venv(venv_path: Path) -> Tuple[bool, str]:
    """
    Run ``python --version`` and ``pip list`` inside the virtual environment.
    Returns ``(success, combined_output)``.
    """
    python_exe = _venv_python_executable(venv_path)
    pip_exe = _venv_pip_executable(venv_path)

    try:
        version_res = subprocess.run(
            [str(python_exe), "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        pip_res = subprocess.run(
            [str(pip_exe), "list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        combined = version_res.stdout + "\n" + pip_res.stdout
        return True, combined
    except subprocess.CalledProcessError as e:
        return False, e.stdout or e.stderr

def write_setup_log(venv_path: Path, content: str) -> Path:
    """
    Write ``content`` to ``venv/setup_log.txt`` and return the path.
    """
    log_path = venv_path / "setup_log.txt"
    log_path.write_text(content, encoding="utf-8")
    return log_path

def main() -> int:
    """
    Orchestrates:
    1. Creation of the virtual environment.
    2. Installation of the pinned requirements.
    3. Verification of the environment (python version + pip list).
    4. Writing of a log file ``venv/setup_log.txt``.
    Exits with ``0`` on success, ``1`` on any failure.
    """
    project_root = get_project_root()
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    # Step 1: create venv
    if not create_venv(venv_path):
        print("[FAIL] Virtual environment creation failed.", file=sys.stderr)
        return 1

    # Step 2: install dependencies
    success, install_output = install_dependencies(venv_path, requirements_path)
    if not success:
        print("[FAIL] Dependency installation failed.", file=sys.stderr)
        print(install_output, file=sys.stderr)
        write_setup_log(venv_path, install_output)
        return 1

    # Step 3: verify installation
    success, verify_output = verify_venv(venv_path)
    if not success:
        print("[FAIL] Verification of virtual environment failed.", file=sys.stderr)

    # Step 4: write log (always write, even if verification failed)
    full_log = (
        "=== Dependency Installation Output ===\n"
        + install_output
        + "\n=== Verification Output ===\n"
        + verify_output
    )
    write_setup_log(venv_path, full_log)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())