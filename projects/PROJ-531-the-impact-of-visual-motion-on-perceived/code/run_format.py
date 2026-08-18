"""
Script to run code formatting (black).
"""
import subprocess
import sys
import os

def main():
    """Run black formatter on the code directory."""
    print("Running black formatter...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "code/"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e.stderr}")
        sys.exit(1)
