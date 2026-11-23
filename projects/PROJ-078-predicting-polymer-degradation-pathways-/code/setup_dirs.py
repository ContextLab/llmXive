"""
T001: Create project directory tree and record its structure.
Writes directory listing to data/reports/ (project-owned) instead of state/.
"""
import os
import subprocess
from pathlib import Path

def main():
    """Create required directory structure and record it."""
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
    
    # Create all directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Record directory tree to project-owned location (data/reports/)
    output_file = Path("data/reports/dir_structure.txt")
    
    try:
        # Try using 'tree' command if available
        with open(output_file, "w") as f:
            result = subprocess.run(
                ["tree", "-a", "."],
                stdout=f,
                stderr=subprocess.DEVNULL,
                text=True
            )
        if result.returncode == 0:
            print(f"Recorded directory structure to {output_file}")
        else:
            raise FileNotFoundError("tree command failed")
    except (FileNotFoundError, OSError):
        # Fallback: use find command
        print("'tree' not available; using 'find' as fallback")
        with open(output_file, "w") as f:
            subprocess.run(
                ["find", ".", "-type", "d", "-o", "-type", "f"],
                stdout=f,
                stderr=subprocess.DEVNULL,
                text=True
            )
        print(f"Recorded directory structure to {output_file}")
    
    # Verify output file is non-empty
    if output_file.stat().st_size > 0:
        print(f"✓ Directory listing written ({output_file.stat().st_size} bytes)")
    else:
        raise RuntimeError(f"Directory listing file is empty: {output_file}")

if __name__ == "__main__":
    main()