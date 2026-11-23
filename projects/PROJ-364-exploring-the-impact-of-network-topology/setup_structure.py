"""
Script to initialize the project directory structure and configuration files.
This ensures a consistent environment for the research pipeline.
"""
import os
import shutil
import sys

# Define the directory structure
DIRECTORIES = [
    "src",
    "tests",
    "data/raw",
    "data/processed",
    "results",
    "state",
    "contracts",
    "logs",
    "docs"
]

def create_structure():
    """Create all necessary directories if they don't exist."""
    created_count = 0
    for dir_path in DIRECTORIES:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")
    
    # Create a placeholder .gitkeep in each to ensure they persist in version control
    for dir_path in DIRECTORIES:
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Placeholder to keep directory in git\n")
            print(f"Created .gitkeep in {dir_path}")
    
    return created_count

def main():
    print("Initializing project structure for PROJ-364...")
    count = create_structure()
    print(f"Setup complete. Created {count} new directories.")
    print("Please ensure requirements.txt, config.yaml, and pyproject.toml are present.")

if __name__ == "__main__":
    main()
