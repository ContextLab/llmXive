import pathlib
import sys

def main():
    """
    Creates the canonical project directory tree as required by T001.
    Directories are created relative to the 'code/' directory.
    """
    # The script is located in <project_root>/code/setup_project_tree.py
    # We define the base as the directory containing this script.
    code_root = pathlib.Path(__file__).parent.resolve()
    
    # Required directory structure relative to code/
    dirs = [
        "src",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "state"
    ]
    
    print(f"Creating project tree under: {code_root}")
    
    try:
        for d in dirs:
            target_dir = code_root / d
            target_dir.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep to ensure empty directories are tracked by version control
            (target_dir / ".gitkeep").touch()
            print(f"Created: {target_dir}")
        
        print("Project directory tree successfully initialized.")
    except Exception as e:
        print(f"Error creating directory tree: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()