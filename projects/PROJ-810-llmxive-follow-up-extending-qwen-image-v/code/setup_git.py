import sys
from pathlib import Path
from utils.git_utils import main as git_main

def main():
    """Entry point for Git repository initialization."""
    project_root = Path(__file__).parent.parent
    try:
        git_main(project_root)
        print("Git repository initialized or already exists.")
        return 0
    except Exception as e:
        print(f"Error initializing Git repository: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
