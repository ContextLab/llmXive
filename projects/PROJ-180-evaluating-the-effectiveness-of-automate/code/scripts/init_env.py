"""
Environment Initialization Script for llmXive Project.

This script initializes the git repository, creates a Python virtual environment,
and installs dependencies from requirements.txt.

Usage:
    python code/scripts/init_env.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a shell command and return the result.

    Args:
        command: List of command arguments.
        cwd: Working directory for the command.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        CompletedProcess instance.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

def init_git(project_root: Path) -> None:
    """
    Initialize a git repository if one does not already exist.

    Args:
        project_root: Path to the project root directory.
    """
    git_dir = project_root / ".git"
    if git_dir.exists():
        print("Git repository already initialized.")
        return

    print("Initializing git repository...")
    run_command(["git", "init"], cwd=project_root)
    print("Git repository initialized successfully.")

def create_venv(project_root: Path, venv_name: str = "venv") -> Path:
    """
    Create a Python virtual environment in the project root.

    Args:
        project_root: Path to the project root directory.
        venv_name: Name of the virtual environment directory.

    Returns:
        Path to the created virtual environment.
    """
    venv_path = project_root / venv_name
    if venv_path.exists():
        print(f"Virtual environment '{venv_name}' already exists.")
        return venv_path

    print(f"Creating virtual environment '{venv_name}'...")
    run_command([sys.executable, "-m", "venv", str(venv_name)], cwd=project_root)
    print(f"Virtual environment '{venv_name}' created successfully.")
    return venv_path

def install_dependencies(project_root: Path, venv_path: Path, requirements_path: Path) -> None:
    """
    Install dependencies from requirements.txt into the virtual environment.

    Args:
        project_root: Path to the project root directory.
        venv_path: Path to the virtual environment.
        requirements_path: Path to requirements.txt.
    """
    if not requirements_path.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")

    # Determine the pip executable path based on OS
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        pip_executable = venv_path / "bin" / "pip"

    if not pip_executable.exists():
        raise RuntimeError(f"Pip executable not found at {pip_executable}")

    print("Installing dependencies...")
    run_command([str(pip_executable), "install", "-r", str(requirements_path)], cwd=project_root)
    print("Dependencies installed successfully.")

def main() -> None:
    """
    Main entry point for the environment initialization script.
    """
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    print(f"Project root: {project_root}")

    # 1. Initialize Git
    init_git(project_root)

    # 2. Create Virtual Environment
    venv_path = create_venv(project_root)

    # 3. Install Dependencies
    requirements_path = project_root / "requirements.txt"
    if requirements_path.exists():
        install_dependencies(project_root, venv_path, requirements_path)
    else:
        print("Warning: requirements.txt not found. Skipping dependency installation.")
        print("Please run 'pip install -r requirements.txt' manually after activating the venv.")

    print("\nSetup complete. To activate the environment:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()
