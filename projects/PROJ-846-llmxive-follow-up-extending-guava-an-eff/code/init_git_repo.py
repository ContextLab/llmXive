import os
import subprocess
import sys
from pathlib import Path
from code.git_operations import init_repository, stage_all_files, commit_changes

def initialize_git_repository(root_path: Path) -> bool:
    """
    Initialize a git repository in the specified path, add all files,
    and create the initial commit.
    
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure the path exists
        if not root_path.exists():
            print(f"Error: Path {root_path} does not exist.", file=sys.stderr)
            return False

        # Initialize repository
        print(f"Initializing git repository at {root_path}...")
        init_repository(root_path)

        # Configure git user if not set (needed for commit)
        subprocess.run(
            ['git', 'config', 'user.email', 'llmxive@example.com'],
            cwd=root_path,
            check=False
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'llmXive Agent'],
            cwd=root_path,
            check=False
        )

        # Stage all files
        print("Staging all files...")
        stage_all_files(root_path)

        # Create initial commit
        print("Creating initial commit...")
        commit_message = "Initial commit"
        commit_changes(root_path, commit_message)

        print("Git repository initialized successfully.")
        return True

    except Exception as e:
        print(f"Failed to initialize git repository: {e}", file=sys.stderr)
        return False

def main():
    """Entry point for git initialization."""
    # Default to current directory if no argument provided
    root_path = Path.cwd()
    
    if len(sys.argv) > 1:
        root_path = Path(sys.argv[1])
    
    success = initialize_git_repository(root_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
