"""
Script to initialize the project directory structure for the Robotic AI Sensory Fidelity Ablation Study.
Creates the necessary folders for source code, scripts, tests, data, and results as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is run.
    # We assume the script is run from the repository root or code/ directory.
    # The task specifies paths relative to project root: code/src/..., code/scripts, etc.
    
    # Determine the base path. If running as script, __file__ is available.
    script_path = Path(__file__).resolve()
    # The script is in code/scripts/, so we go up two levels to get to 'code' or one level if we are at root.
    # The task requires paths like 'code/src/...', so we assume we are at the project root or 'code' folder.
    # Let's assume the command is run from the project root.
    # If the script is in code/scripts, and we want to create code/src, we need to go up to project root.
    
    # Strategy: Look for a marker file or assume standard layout.
    # Based on task description: "mkdir -p code/src/..."
    # We will create a 'code' directory if it doesn't exist, then the subdirectories.
    
    # To be safe regardless of where the script is called from, we treat the parent of 'code' as the root.
    # But the task says "relative to the project root".
    # Let's assume the current working directory is the project root.
    root = Path.cwd()
    
    # Define the directories to create
    dirs_to_create = [
        "code/src/environment",
        "code/src/data",
        "code/src/agents",
        "code/src/analysis",
        "code/src/utils",
        "code/scripts",
        "code/tests",
        "code/data",
        "code/results"
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    
    # Verify structure
    print("\nVerifying structure:")
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())