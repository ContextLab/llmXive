"""
Script to install and verify linting and formatting tools.
This script ensures flake8, pylint, black, and isort are available.
"""
import subprocess
import sys
import os

TOOLS = [
    {"name": "flake8", "pkg": "flake8", "cmd": ["flake8", "--version"]},
    {"name": "pylint", "pkg": "pylint", "cmd": ["pylint", "--version"]},
    {"name": "black", "pkg": "black", "cmd": ["black", "--version"]},
    {"name": "isort", "pkg": "isort", "cmd": ["isort", "--version"]},
]

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None

def install_tools():
    """Install all required linting and formatting tools."""
    print("Installing linting and formatting tools...")
    for tool in TOOLS:
        print(f"  Installing {tool['name']}...")
        result = run_command([sys.executable, "-m", "pip", "install", tool["pkg"]])
        if result and result.returncode == 0:
            print(f"    Success: {tool['name']} installed.")
        else:
            print(f"    Failed to install {tool['name']}.")
            return False
    return True

def verify_tools():
    """Verify that all tools are installed and working."""
    print("\nVerifying tools...")
    all_good = True
    for tool in TOOLS:
        print(f"  Checking {tool['name']}...")
        result = run_command(tool["cmd"], check=False)
        if result and result.returncode == 0:
            # Print first line of version output
            version_line = result.stdout.strip().split('\n')[0]
            print(f"    OK: {version_line}")
        else:
            print(f"    Missing or failed: {tool['name']}")
            all_good = False
    return all_good

def main():
    """Main entry point."""
    print("Setting up linting and formatting environment...")
    
    # Check if tools are already installed
    if not verify_tools():
        print("\nSome tools are missing. Attempting installation...")
        if not install_tools():
            print("\nInstallation failed. Please install tools manually.")
            sys.exit(1)
        
        # Verify again after installation
        if not verify_tools():
            print("\nVerification failed after installation.")
            sys.exit(1)
    
    print("\nLinting and formatting tools are ready.")
    print("Configuration files (.flake8, .pylintrc, pyproject.toml) are present in the project root.")
    print("Run 'black . --check' and 'isort . --check' to verify formatting.")
    print("Run 'flake8 code/' and 'pylint code/' to check for linting issues.")

if __name__ == "__main__":
    main()