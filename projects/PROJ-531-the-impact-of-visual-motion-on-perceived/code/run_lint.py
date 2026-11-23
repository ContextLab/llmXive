"""
Script to run linting (ruff/flake8).
"""
import subprocess
import sys
import os

def run_command(cmd: list) -> int:
    """Run a linting command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed:\n{e.stderr}")
        return 1

def main():
    """Run linters on the code directory."""
    exit_code = 0
    
    # Try ruff first
    exit_code = run_command([sys.executable, "-m", "ruff", "check", "code/"])
    
    # If ruff is not available, try flake8
    if exit_code != 0:
        print("Ruff not found or failed. Trying flake8...")
        exit_code = run_command([sys.executable, "-m", "flake8", "code/"])
    
    sys.exit(exit_code)
