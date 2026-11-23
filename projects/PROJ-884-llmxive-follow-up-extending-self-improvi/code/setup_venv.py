import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional

def find_python311() -> Optional[str]:
    """
    Locate a Python 3.11 interpreter.
    Returns the path to the executable if found, None otherwise.
    """
    candidates = [
        "python3.11",
        "python3", 
        "python"
    ]
    
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if "3.11" in result.stdout or "3.11" in result.stderr:
                return candidate
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # Fallback: try to find python3.11 explicitly if 'python3' didn't match
    try:
        result = subprocess.run(
            ["python3.11", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return "python3.11"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
        
    return None

def create_virtual_environment(project_root: Path, venv_name: str = ".venv") -> bool:
    """
    Create a Python virtual environment in the specified project directory.
    
    Args:
        project_root: The root directory of the project
        venv_name: Name of the virtual environment directory (default: .venv)
        
    Returns:
        True if creation was successful, False otherwise
    """
    venv_path = project_root / venv_name
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
        
    python_executable = find_python311()
    if not python_executable:
        print("ERROR: Could not find Python 3.11. Please install it and try again.")
        return False
        
    try:
        print(f"Creating virtual environment at {venv_path} using {python_executable}...")
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Verify the environment was created correctly
        if not (venv_path / "bin" / "activate").exists():
            print("ERROR: Virtual environment activation script not found.")
            return False
            
        if not (venv_path / "bin" / "python").exists():
            print("ERROR: Python executable not found in virtual environment.")
            return False
            
        print("Virtual environment created successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error creating virtual environment: {e}")
        return False

def install_dependencies(project_root: Path, requirements_path: Optional[Path] = None) -> bool:
    """
    Install dependencies from requirements.txt into the virtual environment.
    
    Args:
        project_root: The root directory of the project
        requirements_path: Optional path to requirements.txt (default: project_root/requirements.txt)
        
    Returns:
        True if installation was successful, False otherwise
    """
    venv_path = project_root / ".venv"
    
    if not venv_path.exists():
        print("ERROR: Virtual environment does not exist. Run create_virtual_environment first.")
        return False
        
    if requirements_path is None:
        requirements_path = project_root / "requirements.txt"
        
    if not requirements_path.exists():
        print(f"WARNING: requirements.txt not found at {requirements_path}. Skipping dependency installation.")
        return True
        
    pip_path = venv_path / "bin" / "pip"
    python_path = venv_path / "bin" / "python"
    
    try:
        print(f"Installing dependencies from {requirements_path}...")
        
        # Upgrade pip first
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Install requirements
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Dependencies installed successfully.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error installing dependencies: {e}")
        return False

def main():
    """Main entry point for the virtual environment setup script."""
    # Determine project root (assuming this script is in code/setup_venv.py)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent.parent
    
    print(f"Project root: {project_root}")
    
    # Create virtual environment
    if not create_virtual_environment(project_root):
        sys.exit(1)
        
    # Install dependencies
    if not install_dependencies(project_root):
        sys.exit(1)
        
    print("\nSetup complete!")
    print(f"To activate the environment, run: source {project_root}/.venv/bin/activate")
    print("Then install any additional project-specific dependencies if needed.")

if __name__ == "__main__":
    main()
