"""
Main entry point to run the directory setup script.
This script is executed to create the required directory structure.
"""
import sys
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from setup_directories import create_directories

def main():
    """Run the directory setup."""
    print("Starting directory structure setup...")
    create_directories()
    print("Setup completed successfully.")

if __name__ == "__main__":
    main()