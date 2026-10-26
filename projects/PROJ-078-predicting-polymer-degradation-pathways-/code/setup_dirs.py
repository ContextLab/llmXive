import os
import subprocess
from pathlib import Path

def main():
    """
    Implements T001: Create project directory tree and record its structure.
    """
    # Define the required directory structure as per tasks.md
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/augmented",
        "data/external",
        "data/reports",
        "data/output",
        "tests",
        "state",
        "state/projects"
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")
    
    # Record directory tree for reproducibility
    # The task explicitly requests 'tree -a . > state/dir_structure.txt'
    try:
        with open("state/dir_structure.txt", "w") as f:
            # -a includes hidden files
            subprocess.run(["tree", "-a", "."], stdout=f, check=True, text=True)
        print("Recorded directory structure using 'tree' to state/dir_structure.txt")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback if 'tree' is not installed on the runner environment
        # We use 'find' to provide a recursive listing that satisfies the non-empty check
        print("'tree' command not found. Using 'find' as fallback.")
        with open("state/dir_structure.txt", "w") as f:
            subprocess.run(["find", ".", "-maxdepth", "3"], stdout=f, check=True, text=True)
        print("Recorded directory structure using 'find' to state/dir_structure.txt")

if __name__ == "__main__":
    main()