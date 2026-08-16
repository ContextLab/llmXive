import sys
from pathlib import Path
from utils.git_utils import main as git_main


def main() -> int:
    """
    Wrapper for git initialization setup.
    
    Returns:
        int: Exit code from git initialization
    """
    # Default to current directory
    project_root = Path.cwd()
    
    # Check if a specific path was provided
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        
    if not project_root.exists():
        print(f"Error: Path '{project_root}' does not exist.")
        return 1
        
    # Change to project root for initialization
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(project_root)
        return git_main()
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    sys.exit(main())
