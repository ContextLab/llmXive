import subprocess
import sys
import os
from pathlib import Path

def get_python_version() -> str:
    """Return the required Python version string."""
    return "3.11"

def check_python_version(required_version: str) -> bool:
    """Check if the current Python version matches the required version."""
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if current_version != required_version:
        print(f"Warning: Current Python version ({current_version}) does not match required version ({required_version}).")
        print("Proceeding anyway, but virtualenv creation may fail if Python 3.11 is not installed.")
        return False
    return True

def create_venv(venv_path: Path, python_version: str) -> bool:
    """Create a virtual environment using the specified Python version."""
    python_executable = f"python{python_version}"
    try:
        # Attempt to create venv with specific python version
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Virtual environment created successfully at {venv_path}")
        return True
    except FileNotFoundError:
        print(f"Error: Python {python_version} executable not found. Please install Python {python_version}.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr.decode()}")
        return False

def install_dependencies(venv_path: Path, requirements_file: Path) -> bool:
    """Install dependencies from requirements.txt into the virtual environment."""
    if not requirements_file.exists():
        print(f"Error: Requirements file not found at {requirements_file}")
        return False

    venv_bin = venv_path / "bin" if os.name != "nt" else venv_path / "Scripts"
    pip_executable = venv_bin / "pip"

    if not pip_executable.exists():
        print(f"Error: pip not found in virtual environment at {pip_executable}")
        return False

    try:
        print(f"Installing dependencies from {requirements_file}...")
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_file)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e.stderr.decode()}")
        return False

def main():
    """Main entry point for virtual environment setup."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    requirements_file = project_root / "code" / "requirements.txt"
    python_version = get_python_version()

    print(f"Setting up Python {python_version} virtual environment...")

    if not check_python_version(python_version):
        print("Continuing with available Python version...")

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing it first.")
        import shutil
        shutil.rmtree(venv_path)

    if create_venv(venv_path, python_version):
        if install_dependencies(venv_path, requirements_file):
            print("\nSetup complete!")
            print(f"Activate the virtual environment with:")
            if os.name == "nt":
                print(f"  venv\\Scripts\\activate.bat")
            else:
                print(f"  source venv/bin/activate")
            return 0
    else:
        print("\nSetup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())