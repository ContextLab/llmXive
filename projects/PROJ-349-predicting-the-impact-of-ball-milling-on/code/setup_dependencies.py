"""
Setup script to install pinned dependencies from requirements.txt.
Ensures the Python environment matches the project specifications.
"""
import subprocess
import sys
from pathlib import Path

def check_installation(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def install_dependencies(requirements_path: Path) -> None:
    """
    Install dependencies from the requirements file.
    
    Args:
        requirements_path: Path to requirements.txt
        
    Raises:
        SystemExit: If installation fails
    """
    if not requirements_path.exists():
        print(f"Error: Requirements file not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point for dependency setup."""
    # Determine project root (assuming script is in code/ or code/code/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "code" else script_dir
    
    requirements_path = project_root / "requirements.txt"
    
    print(f"Project root: {project_root}")
    print(f"Requirements file: {requirements_path}")
    
    # Install dependencies
    install_dependencies(requirements_path)
    
    # Verify critical packages
    critical_packages = [
        "pandas", "numpy", "scikit-learn", "matplotlib", 
        "requests", "tqdm", "pyarrow", "pdfminer.six"
    ]
    
    print("\nVerifying critical packages...")
    all_installed = True
    for pkg in critical_packages:
        # Handle pdfminer.six special case
        import_name = "pdfminer" if pkg == "pdfminer.six" else pkg
        if check_installation(import_name):
            print(f"  [OK] {pkg}")
        else:
            print(f"  [FAIL] {pkg}")
            all_installed = False

    if not all_installed:
        print("\nWarning: Some critical packages are missing.")
        sys.exit(1)
    
    print("\nAll dependencies verified successfully.")

if __name__ == "__main__":
    main()
