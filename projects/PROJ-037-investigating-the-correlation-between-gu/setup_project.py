"""
Script to initialize the project directory structure for PROJ-037.
Creates all required directories and placeholder files as specified in T001a.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the current working directory
    project_root = Path("projects/PROJ-037-investigating-the-correlation-between-gu")
    
    # Define all directories to create
    directories = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code",
        "tests",
        "docs",
        # Additional standard directories for a robust structure
        "figures",
        "logs",
        "specs",
    ]
    
    # Define files to create (empty)
    files = [
        "README.md",
        ".gitignore",
    ]
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {full_path}")
    
    # Create empty files
    for file_path in files:
        full_path = project_root / file_path
        if not full_path.exists():
            full_path.touch()
            print(f"  Created file: {full_path}")
        else:
            print(f"  File already exists: {full_path}")
    
    # Create .gitignore content if it's empty or missing standard entries
    gitignore_path = project_root / ".gitignore"
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environments
venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Data
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/outputs/*
!data/outputs/.gitkeep

# Logs
logs/*
!logs/.gitkeep

# OS
.DS_Store
Thumbs.db
"""
    # Only write if file is empty or doesn't exist
    if gitignore_path.stat().st_size == 0:
        with open(gitignore_path, "w") as f:
            f.write(gitignore_content.strip())
        print(f"  Updated .gitignore with standard entries")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    keep_dirs = ["data/raw", "data/processed", "data/outputs"]
    for dir_path in keep_dirs:
        keep_file = project_root / dir_path / ".gitkeep"
        keep_file.touch()
        print(f"  Created .gitkeep in: {project_root / dir_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()