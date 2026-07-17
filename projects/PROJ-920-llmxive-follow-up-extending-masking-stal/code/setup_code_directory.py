"""
Script to create the 'code/' directory for the llmXive project.
This addresses Task T004.
"""
import os
from pathlib import Path

def main():
    # Determine the project root. Since this script is inside 'code/',
    # we go up one level to find the project root.
    # However, to be robust, we assume the script is run from the project root
    # or the path is relative to the current working directory.
    # The task specifies: Create directory `code/` in `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`
    
    # We will create the directory relative to the current working directory (CWD).
    # The user should run this from the project root.
    project_root = Path.cwd()
    target_dir = project_root / "code"

    if target_dir.exists():
        print(f"Directory '{target_dir}' already exists.")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Successfully created directory: {target_dir}")

if __name__ == "__main__":
    main()