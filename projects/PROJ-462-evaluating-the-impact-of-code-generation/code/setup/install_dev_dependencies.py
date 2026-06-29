"""
Install development dependencies for the code generation impact evaluation project.

This script installs black formatter and other development tools needed for
maintaining code quality in the project.

Usage:
    python code/setup/install_dev_dependencies.py

Dependencies:
    - code/requirements-dev.txt (must exist with development dependencies listed)
"""
import os
import subprocess
import sys
from pathlib import Path


def get_venv_paths():
    """
    Get the paths to the virtual environment Python and pip.

    Returns:
        tuple: (python_path, pip_path) as Path objects
    """
    # Determine virtual environment paths
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        # Virtual environment is active
        venv_path = Path(sys.prefix)
    else:
        # No virtual environment active - use current environment
        venv_path = Path(sys.prefix)

    python_path = venv_path / 'bin' / 'python' if os.name != 'nt' else venv_path / 'Scripts' / 'python.exe'
    pip_path = venv_path / 'bin' / 'pip' if os.name != 'nt' else venv_path / 'Scripts' / 'pip.exe'

    return python_path, pip_path


def create_virtual_environment(env_path=None):
    """
    Create a virtual environment if one doesn't exist.

    Args:
        env_path: Path to the virtual environment (optional)

    Returns:
        Path: Path to the virtual environment
    """
    if env_path is None:
        # Default to .venv in project root
        env_path = Path.cwd() / '.venv'

    if not env_path.exists():
        print(f"Creating virtual environment at {env_path}...")
        subprocess.check_call([sys.executable, '-m', 'venv', str(env_path)])
        print(f"Virtual environment created at {env_path}")
    else:
        print(f"Virtual environment already exists at {env_path}")

    return env_path


def install_dependencies(pip_path, requirements_file):
    """
    Install dependencies from a requirements file.

    Args:
        pip_path: Path to the pip executable
        requirements_file: Path to the requirements.txt file

    Returns:
        bool: True if installation succeeded, False otherwise
    """
    if not requirements_file.exists():
        print(f"Error: Requirements file not found at {requirements_file}")
        return False

    print(f"Installing development dependencies from {requirements_file}...")

    try:
        result = subprocess.run(
            [str(pip_path), 'install', '-r', str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Development dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def verify_installation(python_path, package_name='black'):
    """
    Verify that a package was installed successfully.

    Args:
        python_path: Path to the Python executable
        package_name: Name of the package to verify

    Returns:
        bool: True if package is installed, False otherwise
    """
    print(f"Verifying {package_name} installation...")

    try:
        result = subprocess.run(
            [str(python_path), '-m', 'pip', 'show', package_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"{package_name} is installed:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError:
        print(f"Error: {package_name} is not installed")
        return False


def main():
    """
    Main entry point for installing development dependencies.
    """
    # Get project root (parent of code/ directory)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent

    requirements_file = code_dir / 'requirements-dev.txt'

    print("=" * 60)
    print("Installing Development Dependencies")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Requirements file: {requirements_file}")
    print()

    # Check if requirements file exists
    if not requirements_file.exists():
        print(f"Error: Requirements file not found at {requirements_file}")
        print("Please create code/requirements-dev.txt with development dependencies.")
        sys.exit(1)

    # Get virtual environment paths
    python_path, pip_path = get_venv_paths()

    # Check if pip exists
    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}")
        print("Please activate the virtual environment first or create one.")
        sys.exit(1)

    # Install dependencies
    success = install_dependencies(pip_path, requirements_file)

    if not success:
        print("Failed to install development dependencies.")
        sys.exit(1)

    # Verify black installation
    if verify_installation(python_path, 'black'):
        print("=" * 60)
        print("Development environment setup complete!")
        print("=" * 60)
        print("You can now format code with: black code/")
        print("Or: python -m black code/")
    else:
        print("Warning: Could not verify black installation.")
        sys.exit(1)


if __name__ == '__main__':
    main()
