import os
import sys
import subprocess
from pathlib import Path

def main():
    """Setup linting tools (ruff and black) if not already installed."""
    print("Setting up linting tools...")
    
    # Check if ruff is installed
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], 
                     check=True, capture_output=True)
        print("✓ ruff is already installed")
    except subprocess.CalledProcessError:
        print("Installing ruff...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)
    
    # Check if black is installed
    try:
        subprocess.run([sys.executable, "-m", "black", "--version"], 
                     check=True, capture_output=True)
        print("✓ black is already installed")
    except subprocess.CalledProcessError:
        print("Installing black...")
        subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True)
    
    print("Linting tools setup complete.")

if __name__ == "__main__":
    main()