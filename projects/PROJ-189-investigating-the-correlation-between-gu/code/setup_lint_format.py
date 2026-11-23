"""
Script to configure and install linting (ruff) and formatting (black) tools.
This script ensures the necessary dependencies are installed and configuration
files exist in the project root.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=False,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if check:
            sys.exit(1)
        return e

def ensure_config_files() -> None:
    """Ensure pyproject.toml exists with black and ruff configurations."""
    # The pyproject.toml is already created by this task implementation.
    # This function serves as a placeholder for future logic if dynamic config generation is needed.
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "pyproject.toml"
    
    if not config_file.exists():
        print(f"Warning: {config_file} not found. Please ensure it exists.")
    else:
        print(f"Configuration file found: {config_file}")

def install_dependencies() -> None:
    """Install ruff and black using pip."""
    packages = ["ruff", "black"]
    for pkg in packages:
        try:
            # Check if already installed
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"{pkg} is already installed.")
        except subprocess.CalledProcessError:
            print(f"Installing {pkg}...")
            run_command([sys.executable, "-m", "pip", "install", pkg])

def main() -> None:
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools...")
    
    # 1. Install dependencies
    install_dependencies()
    
    # 2. Ensure config files exist
    ensure_config_files()
    
    # 3. Run a dry-run of ruff to verify configuration
    print("\nVerifying ruff configuration...")
    run_command(["ruff", "check", "--output-format=concise", "."], check=False)
    
    # 4. Run a dry-run of black to verify configuration
    print("\nVerifying black configuration...")
    run_command(["black", "--check", "--diff", "."], check=False)
    
    print("\nSetup complete. Run 'ruff check .' and 'black --check .' to verify style.")

if __name__ == "__main__":
    main()
