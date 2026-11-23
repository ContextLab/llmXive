import subprocess
import sys
import os
from pathlib import Path
from config import PROJECT_ROOT

def get_flake8_config_path():
    """Return the path to the .flake8 configuration file."""
    return PROJECT_ROOT / ".flake8"

def get_black_config_path():
    """Return the path to the pyproject.toml configuration file (used by black)."""
    return PROJECT_ROOT / "pyproject.toml"

def setup_flake8_config():
    """Ensure .flake8 configuration exists at project root."""
    flake8_path = get_flake8_config_path()
    if not flake8_path.exists():
        print(f"Warning: {flake8_path} not found. Please create it manually.")
        return False
    return True

def setup_black_config():
    """Ensure pyproject.toml with black configuration exists at project root."""
    black_path = get_black_config_path()
    if not black_path.exists():
        print(f"Warning: {black_path} not found. Please create it manually.")
        return False
    return True

def install_tools():
    """Install flake8 and black if not already installed."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flake8", "black"])
        print("Successfully installed flake8 and black.")
    except subprocess.CalledProcessError:
        print("Failed to install flake8 or black. Please install them manually.")
        return False
    return True

def run_formatting():
    """Run black formatting on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        print(f"Warning: {code_dir} does not exist.")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Formatting completed successfully.")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e.stderr}")
        return False

def run_linting():
    """Run flake8 linting on the code directory."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        print(f"Warning: {code_dir} does not exist.")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Linting completed successfully (no issues found).")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Linting found issues:\n{e.stdout}")
        return False

def main():
    """Main entry point for linting and formatting setup."""
    print("Setting up linting and formatting tools...")
    
    if not install_tools():
        return 1

    if not setup_flake8_config():
        return 1
    
    if not setup_black_config():
        return 1

    print("\nConfiguration files verified.")
    print("Run 'python code/linting_config.py format' to format code.")
    print("Run 'python code/linting_config.py lint' to check code.")
    return 0

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "format":
            success = run_formatting()
        elif command == "lint":
            success = run_linting()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
        sys.exit(0 if success else 1)
    else:
        sys.exit(main())