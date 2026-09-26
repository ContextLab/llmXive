"""
Script to initialize project directory structure.
"""
from config import ensure_directories
from pathlib import Path
import sys

def main():
    """Create project directories."""
    print("Initializing project directory structure...")
    created = ensure_directories()
    for d in created:
        print(f"Created: {d}")
    print("Directory initialization complete.")

if __name__ == "__main__":
    main()
