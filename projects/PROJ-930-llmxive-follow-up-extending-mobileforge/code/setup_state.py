import os
import sys
from pathlib import Path

from utils.state_manager import initialize_state_structure, get_state_summary

def main():
    """
    Setup script to initialize the state directory for artifact checksums and versioning.
    Implements Constitution Principle III.
    """
    project_root = Path.cwd()
    print(f"Initializing state directory structure at: {project_root}")
    
    state_dir = initialize_state_structure(project_root)
    print(f"State directory created at: {state_dir}")
    
    summary = get_state_summary(project_root)
    print(f"State summary: {summary}")
    
    print("State initialization complete.")

if __name__ == "__main__":
    main()
