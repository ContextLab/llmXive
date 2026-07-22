import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-550.
    Creates the required folder hierarchy under projects/PROJ-550-exploring-the-convergence-of-iterated-fu/.
    """
    project_root = Path("projects/PROJ-550-exploring-the-convergence-of-iterated-fu")
    
    # Define the subdirectories to create based on task T001 requirements
    subdirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests/unit",
        "tests/contract",
        "docs"
    ]
    
    # Create directories
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create placeholder files to ensure directories are not empty and ready for use
    # This helps in immediate verification and prevents issues with empty directory handling in some tools
    (project_root / "README.md").touch(exist_ok=True)
    (project_root / "data" / ".gitkeep").touch(exist_ok=True)
    (project_root / "tests" / ".gitkeep").touch(exist_ok=True)
    
    print(f"Project structure initialized at: {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())