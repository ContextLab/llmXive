import os
import subprocess
import sys
import shutil
from pathlib import Path

def check_requirements_exists(project_root: Path) -> bool:
    """Check if requirements.txt exists in the project root."""
    req_file = project_root / "requirements.txt"
    if not req_file.exists():
        print(f"Error: requirements.txt not found at {req_file}")
        return False
    return True

def create_venv(project_root: Path, venv_name: str = "venv") -> Path:
    """Create a virtual environment in the project root."""
    venv_path = project_root / venv_name
    
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Removing...")
        shutil.rmtree(venv_path)
    
    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.stderr.decode()}")
        sys.exit(1)

def get_venv_python(venv_path: Path) -> Path:
    """Get the path to the Python executable in the virtual environment."""
    if os.name == "nt":  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        return venv_path / "bin" / "python"

def install_dependencies(venv_python: Path, requirements_path: Path) -> None:
    """Install dependencies from requirements.txt into the virtual environment."""
    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # First, upgrade pip to ensure compatibility
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Pip upgraded successfully.")
        
        # Install requirements
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Dependencies installed successfully.")
        
        # Print installation summary
        print("\n--- Installation Log ---")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e.stderr}")
        sys.exit(1)

def main():
    """Main entry point for setting up the virtual environment."""
    # Determine project root (assuming script is in code/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    
    # Check for requirements.txt
    if not check_requirements_exists(project_root):
        sys.exit(1)
    
    requirements_path = project_root / "requirements.txt"
    
    # Create virtual environment
    venv_path = create_venv(project_root)
    
    # Get venv python executable
    venv_python = get_venv_python(venv_path)
    
    # Install dependencies
    install_dependencies(venv_python, requirements_path)
    
    print(f"\nSetup complete!")
    print(f"Activate the environment with:")
    if os.name == "nt":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")
    
    # Verify installation by listing packages
    print("\nInstalled packages:")
    result = subprocess.run(
        [str(venv_python), "-m", "pip", "freeze"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    print(result.stdout)

if __name__ == "__main__":
    main()
