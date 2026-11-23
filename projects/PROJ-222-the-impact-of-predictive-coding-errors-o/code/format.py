"""
Formatting utility for running black on the project codebase.
"""
import subprocess
import sys
import os

def run_command(command: list) -> int:
    """Run a formatting command and return the exit code."""
    try:
        result = subprocess.run(command, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it via 'pip install black'.")
        return 1

def main():
    """Main entry point for running formatters."""
    print("Running formatters...")
    
    # Run black
    exit_code = run_command([sys.executable, "-m", "black", "code/"])
    
    if exit_code == 0:
        print("Formatting complete!")
    else:
        print("Formatting encountered issues.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
