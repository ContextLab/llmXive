"""
Setup script for PROJ-227-assessing-the-trade-offs-between-static-

Creates the required project directory structure as specified in T001.
"""
import os
from pathlib import Path

# Define the project root relative to the current working directory
# The task assumes we are running from the repository root
PROJECT_ROOT = Path.cwd()
PROJECT_NAME = "PROJ-227-assessing-the-trade-offs-between-static-"

# Define the base path for the project
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

# Define the directories to create based on T001 requirements
DIRECTORIES_TO_CREATE = [
    PROJECT_DIR / "data" / "raw",
    PROJECT_DIR / "data" / "processed",
    PROJECT_DIR / "state",
    PROJECT_DIR / "code",
    PROJECT_DIR / "tests",
]

def main():
    """Create the directory structure if it doesn't exist."""
    print(f"Setting up project directory structure at: {PROJECT_DIR}")
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in DIRECTORIES_TO_CREATE:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists: {dir_path}")
            skipped_count += 1
    
    print(f"Setup complete. Created {created_count} directories, skipped {skipped_count} existing.")
    
    # Verify structure
    assert PROJECT_DIR.exists(), "Project root directory not created"
    assert (PROJECT_DIR / "data" / "raw").exists(), "data/raw not created"
    assert (PROJECT_DIR / "data" / "processed").exists(), "data/processed not created"
    assert (PROJECT_DIR / "state").exists(), "state not created"
    assert (PROJECT_DIR / "code").exists(), "code not created"
    assert (PROJECT_DIR / "tests").exists(), "tests not created"
    
    print("Verification passed: All required directories exist.")

if __name__ == "__main__":
    main()
