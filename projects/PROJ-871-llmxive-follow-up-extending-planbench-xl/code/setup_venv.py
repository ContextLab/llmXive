"""
Virtual environment setup script for the Project PROJ-871-llmxive-follow-up-extending-planbench-xl.

This script creates a Python ``venv`` inside the project root, installs the
pinned packages from ``requirements.txt`` into it, and records a verification
log containing both the Python interpreter version and the list of installed
packages.

The public API (functions and signatures) matches the contract defined in the
project's task description and is used by the test suite.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# ----------------------------------------------------------------------
# Helper functions to locate the interpreter / pip inside a virtual env
# ----------------------------------------------------------------------
def _venv_python_executable(venv_path: Path) -> Path:
    """Return the absolute path to the Python interpreter inside ``venv_path``."""
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def _venv_pip_executable(venv_path: Path) -> Path:
    """Return the absolute path to the ``pip`` executable inside ``venv_path``."""
    if os.name == "nt":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


# ----------------------------------------------------------------------
# Core orchestration functions (public API)
# ----------------------------------------------------------------------
def create_venv(venv_path: Path) -> bool:
    """
    Create a Python virtual environment at ``venv_path`` using ``python -m venv``.

    Returns
    -------
    bool
        ``True`` if the environment was created successfully, ``False`` otherwise.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e}", file=sys.stderr)
        return False


def install_dependencies(
    venv_path: Path, requirements_path: Path
) -> Tuple[bool, str]:
    """
    Install the packages listed in ``requirements_path`` into the virtual environment.

    Parameters
    ----------
    venv_path : Path
        Path to the virtual environment directory.
    requirements_path : Path
        Path to the ``requirements.txt`` file.

    Returns
    -------
    Tuple[bool, str]
        ``(success, combined_output)`` where ``success`` indicates whether the
        ``pip install`` command completed without error and ``combined_output``
        contains the stdout+stderr of the installation process.
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
    Verify that the virtual environment works by capturing ``python --version`` and
    ``pip list`` output.

    Returns
    -------
    Tuple[bool, str]
        ``(success, combined_output)`` where ``combined_output`` contains the
        version line followed by the package list.
    """
    python_exe = _venv_python_executable(venv_path)
    pip_exe = _venv_pip_executable(venv_path)

    try:
        # python --version
        ver_res = subprocess.run(
            [str(python_exe), "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # pip list
        list_res = subprocess.run(
            [str(pip_exe), "list"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        combined = ver_res.stdout.strip() + "\n" + list_res.stdout.strip()
        return True, combined
    except subprocess.CalledProcessError as e:
        return False, e.stdout or e.stderr


def write_setup_log(venv_path: Path, content: str) -> Path:
    """
    Write ``content`` to ``venv/setup_log.txt`` and return the path to the file.

    Parameters
    ----------
    venv_path : Path
        Path to the virtual environment directory.
    content : str
        Text to write to the log file.

    Returns
    -------
    Path
        The absolute path to ``setup_log.txt``.
    """
    log_path = venv_path / "setup_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(content, encoding="utf-8")
    return log_path


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Orchestrates the full virtual‑environment creation workflow.

    Steps
    -----
    1. Create ``venv`` under the project root.
    2. Install the pinned dependencies from ``requirements.txt``.
    3. Run ``python --version`` and ``pip list`` inside the venv.
    4. Write the combined output to ``venv/setup_log.txt``.

    Returns
    -------
    int
        Exit code: ``0`` on success, ``1`` on any failure.
    """
    # Resolve project root – the directory that contains the ``code`` folder.
    project_root = Path(__file__).resolve().parents[1]

    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    # ------------------------------------------------------------------
    # Step 1 – create the venv
    # ------------------------------------------------------------------
    if not create_venv(venv_path):
        print("Virtual environment creation failed.", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Step 2 – install dependencies
    # ------------------------------------------------------------------
    success, install_output = install_dependencies(venv_path, requirements_path)
    if not success:
        print("Dependency installation failed.", file=sys.stderr)
        # Still write whatever output we captured for debugging.
        write_setup_log(venv_path, install_output)
        return 1

    # ------------------------------------------------------------------
    # Step 3 – verification (python version + pip list)
    # ------------------------------------------------------------------
    ver_success, ver_output = verify_venv(venv_path)
    if not ver_success:
        print("Virtual environment verification failed.", file=sys.stderr)
        # Combine install output with verification output for full context.
        write_setup_log(venv_path, install_output + "\n" + ver_output)
        return 1

    # ------------------------------------------------------------------
    # Step 4 – write the final log
    # ------------------------------------------------------------------
    full_log = install_output + "\n" + ver_output
    write_setup_log(venv_path, full_log)

    print(f"Virtual environment ready. Log written to {venv_path / 'setup_log.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
