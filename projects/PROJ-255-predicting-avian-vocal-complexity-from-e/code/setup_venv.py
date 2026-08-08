"""
Task T002c: Setup virtual environment and install dependencies.

This script creates a virtual environment, upgrades pip, and installs
all dependencies from requirements.txt. It also runs 'pip check' to
verify no dependency conflicts exist.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path


def get_python_executable():
    """Get the path to the current Python executable."""
    return sys.executable


def run_command(cmd, check=True):
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command to run (list of strings)
        check: If True, raise CalledProcessError on non-zero exit
        
    Returns:
        subprocess.CompletedProcess instance
    """
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise


def setup_venv(venv_path):
    """
    Create a virtual environment at the specified path.
    
    Args:
        venv_path: Path where the virtual environment will be created
    """
    print(f"Creating virtual environment at: {venv_path}")
    cmd = [get_python_executable(), "-m", "venv", str(venv_path)]
    run_command(cmd)
    print("Virtual environment created successfully.")


def activate_and_upgrade_pip(venv_path):
    """
    Upgrade pip inside the virtual environment.
    
    Args:
        venv_path: Path to the virtual environment
    """
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        # Windows compatibility
        pip_path = venv_path / "Scripts" / "pip"
    
    print("Upgrading pip...")
    cmd = [str(pip_path), "install", "--upgrade", "pip"]
    run_command(cmd)
    print("pip upgraded successfully.")


def install_requirements(venv_path, requirements_path):
    """
    Install dependencies from requirements.txt into the virtual environment.
    
    Args:
        venv_path: Path to the virtual environment
        requirements_path: Path to requirements.txt
    """
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        # Windows compatibility
        pip_path = venv_path / "Scripts" / "pip"
    
    print(f"Installing dependencies from: {requirements_path}")
    cmd = [str(pip_path), "install", "-r", str(requirements_path)]
    run_command(cmd)
    print("Dependencies installed successfully.")


def run_pip_check(venv_path):
    """
    Run pip check to verify no dependency conflicts.
    
    Args:
        venv_path: Path to the virtual environment
        
    Returns:
        True if no conflicts found, False otherwise
    """
    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        # Windows compatibility
        pip_path = venv_path / "Scripts" / "pip"
    
    print("Running pip check...")
    cmd = [str(pip_path), "check"]
    try:
        run_command(cmd, check=True)
        print("No dependency conflicts found.")
        return True
    except subprocess.CalledProcessError:
        print("WARNING: Dependency conflicts detected!")
        return False


def main():
    """
    Main entry point for the virtual environment setup script.
    
    This function:
    1. Creates a virtual environment at 'code/.venv'
    2. Upgrades pip
    3. Installs dependencies from 'requirements.txt'
    4. Runs 'pip check' to verify no conflicts
    """
    # Determine project root (parent of 'code' directory)
    code_dir = Path(__file__).parent
    project_root = code_dir.parent
    requirements_path = project_root / "requirements.txt"
    venv_path = code_dir / ".venv"
    
    print("=" * 60)
    print("Task T002c: Setup Virtual Environment")
    print("=" * 60)
    
    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)
    
    # Remove existing venv if it exists (for clean setup)
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)
    
    # Setup virtual environment
    setup_venv(venv_path)
    
    # Upgrade pip
    activate_and_upgrade_pip(venv_path)
    
    # Install requirements
    install_requirements(venv_path, requirements_path)
    
    # Run pip check
    success = run_pip_check(venv_path)
    
    print("=" * 60)
    if success:
        print("Task T002c COMPLETED SUCCESSFULLY")
        print(f"Virtual environment ready at: {venv_path}")
        print("Activate with: source code/.venv/bin/activate")
    else:
        print("Task T002c COMPLETED WITH WARNINGS (dependency conflicts detected)")
        print("Please review the conflicts and resolve them.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
