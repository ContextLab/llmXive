import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list[str]) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(command)}")
        print(f"Error: {e.stderr}")
        return False

def ensure_config_files_exist():
    """Ensure that configuration files for black, flake8, and mypy exist."""
    base_dir = Path(__file__).parent.parent
    config_files = [
        base_dir / ".flake8",
        base_dir / "pyproject.toml",
        base_dir / "mypy.ini",
    ]

    missing = []
    for file_path in config_files:
        if not file_path.exists():
            missing.append(file_path.name)

    if missing:
        print(f"Missing configuration files: {', '.join(missing)}")
        print("Please ensure these files are created manually or by the setup script.")
        return False
    
    print("All configuration files found.")
    return True

def install_tools():
    """Install linting tools (black, flake8, mypy) if not already installed."""
    tools = ["black", "flake8", "mypy"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"Successfully installed {tool}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}. Please install manually.")
            return False
    return True

def main():
    """Main entry point for tooling setup."""
    print("Setting up linting and formatting tools...")
    
    if not install_tools():
        sys.exit(1)
    
    if not ensure_config_files_exist():
        sys.exit(1)
    
    print("Tooling setup complete.")
    sys.exit(0)

if __name__ == "__main__":
    main()