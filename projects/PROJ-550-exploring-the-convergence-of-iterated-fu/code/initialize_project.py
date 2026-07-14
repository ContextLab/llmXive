import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-550.
    Creates the required directories under the project root.
    """
    # Define the project root relative to this file's location (code/)
    # Assuming the script is run from the project root or code/ directory.
    # We use the parent of this file's directory as the base if run from code/,
    # but the task implies a specific project path.
    # To be robust, we create the structure relative to the current working directory
    # or the script's parent if we assume standard project layout.
    
    # Based on the task: projects/PROJ-550-exploring-the-convergence-of-iterated-fu/...
    # We will create this relative to the current working directory.
    
    project_root = Path.cwd()
    project_name = "PROJ-550-exploring-the-convergence-of-iterated-fu"
    base_path = project_root / "projects" / project_name
    
    dirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests/unit",
        "tests/contract",
        "docs"
    ]
    
    print(f"Creating project structure at: {base_path}")
    
    created_count = 0
    for dir_name in dirs:
        target_dir = base_path / dir_name
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {target_dir}")
            created_count += 1
        else:
            print(f"  Exists:  {target_dir}")
    
    print(f"Project structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
