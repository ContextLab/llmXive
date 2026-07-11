"""
Script to run format checks (black/ruff) if installed.
"""
import subprocess
import sys
import os

def run_command(cmd: List[str]) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run format checks."""
    print("Checking code formatting...")
    
    # Check for black
    if run_command(["black", "--check", "code"]):
        print("Black check passed.")
    else:
        print("Black check failed.")
        
    # Check for ruff
    if run_command(["ruff", "check", "code"]):
        print("Ruff check passed.")
    else:
        print("Ruff check failed.")
