"""
Setup script for the project.
This script orchestrates the creation of the project structure.
"""
import os
import sys
from pathlib import Path

# Import from the create_project_structure module
from scripts.create_project_structure import create_directories

def main():
    """Main entry point for project setup."""
    print("Setting up project structure...")
    success = create_directories()
    
    if success:
        print("\nProject setup complete.")
        print("Next steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Configure linting/formatting: black, ruff")
        print("  3. Begin implementing user stories")
    else:
        print("\nProject setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
