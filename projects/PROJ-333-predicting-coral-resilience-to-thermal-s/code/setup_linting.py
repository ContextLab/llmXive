"""
Script to install and verify linting and formatting tools.
This script ensures ruff and black are installed and can be run.
"""
import subprocess
import sys
import os

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            check=check, 
            capture_output=True, 
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def install_tools():
    """Install ruff and black if not present."""
    print("Checking/Installing linting tools...")
    
    # Check if pip is available
    if not run_command([sys.executable, "-m", "pip", "--version"], check=False):
        print("pip not found. Please install pip.")
        return False

    # Install ruff
    if not run_command([sys.executable, "-m", "pip", "install", "ruff"]):
        return False

    # Install black
    if not run_command([sys.executable, "-m", "pip", "install", "black"]):
        return False

    return True

def verify_tools():
    """Verify that ruff and black are executable."""
    print("Verifying tool installation...")
    
    # Verify ruff
    if not run_command(["ruff", "--version"], check=False):
        print("ruff is not installed or not in PATH.")
        return False
        
    # Verify black
    if not run_command(["black", "--version"], check=False):
        print("black is not installed or not in PATH.")
        return False
        
    print("Tools verified successfully.")
    return True

def main():
    """Main entry point."""
    # Ensure we are in the project root or code directory
    # The script is in code/, so we assume project root is parent
    if not install_tools():
        sys.exit(1)
    
    if not verify_tools():
        sys.exit(1)
        
    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()