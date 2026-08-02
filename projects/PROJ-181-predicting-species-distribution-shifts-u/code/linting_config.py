import subprocess
import sys
import os
from pathlib import Path
from config import PROJECT_ROOT

def get_black_config_path() -> Path:
    """Return the path to the black configuration file."""
    return PROJECT_ROOT / "pyproject.toml"

def get_flake8_config_path() -> Path:
    """Return the path to the flake8 configuration file."""
    return PROJECT_ROOT / "code" / ".flake8"

def setup_black_config() -> bool:
    """Ensure black is installed and configuration exists."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Black is not installed or not in PATH.")
            return False
        return True
    except FileNotFoundError:
        print("Python executable not found.")
        return False

def setup_flake8_config() -> bool:
    """Ensure flake8 is installed and configuration exists."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Flake8 is not installed or not in PATH.")
            return False
        return True
    except FileNotFoundError:
        print("Python executable not found.")
        return False

def install_tools() -> bool:
    """Install black and flake8 if not present."""
    tools = ["black", "flake8", "isort"]
    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            return False
    return True

def run_formatting(target_dir: str = None) -> bool:
    """Run black formatter on the target directory."""
    if target_dir is None:
        target_dir = str(PROJECT_ROOT / "code")
    
    config_path = get_black_config_path()
    cmd = [
        sys.executable, "-m", "black",
        "--config", str(config_path),
        target_dir
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e.stderr}")
        return False

def run_linting(target_dir: str = None) -> bool:
    """Run flake8 linter on the target directory."""
    if target_dir is None:
        target_dir = str(PROJECT_ROOT / "code")
    
    config_path = get_flake8_config_path()
    cmd = [
        sys.executable, "-m", "flake8",
        "--config", str(config_path),
        target_dir
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Linting failed: {e.stderr}")
        return False

def main():
    """Main entry point for linting configuration setup and execution."""
    print("Setting up linting tools...")
    
    # Install tools if necessary
    if not setup_black_config():
        print("Attempting to install black...")
        if not install_tools():
            print("Failed to install tools. Exiting.")
            return 1
    
    if not setup_flake8_config():
        print("Attempting to install flake8...")
        if not install_tools():
            print("Failed to install tools. Exiting.")
            return 1

    print("Running formatting...")
    if not run_formatting():
        print("Formatting failed.")
        # Do not exit with error for formatting, just report
    
    print("Running linting...")
    if not run_linting():
        print("Linting failed.")
        return 1
    
    print("Linting and formatting complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())