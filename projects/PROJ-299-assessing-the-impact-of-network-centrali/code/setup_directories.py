"""
T007: Setup directory structure for data/raw/, data/processed/, data/analysis/, outputs/
and ensure .gitignore rules are in place.

This script is idempotent and can be run multiple times safely.
It creates the necessary directories and placeholder .gitkeep files
to ensure the directory structure is preserved in version control.
"""
import os
import sys
from pathlib import Path

def ensure_directory_structure():
    """Create the required directory structure and .gitkeep files."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the required directories
    directories = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "outputs"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            # Create a .gitkeep file to ensure the directory is tracked
            keep_file = full_path / ".gitkeep"
            if not keep_file.exists():
                keep_file.write_text(
                    "# This file ensures the directory is tracked by git.\n"
                    "# Do not place actual data files here.\n"
                )
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Verify .gitignore exists and contains large file rules
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        print("Warning: .gitignore not found. Creating a basic one.")
        create_gitignore(project_root)
    else:
        print(f".gitignore exists at: {gitignore_path}")
    
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
        print("Directory structure is ready for the pipeline.")
    else:
        print("\nNo new directories were created. Structure already exists.")

def create_gitignore(root_path: Path):
    """Create a .gitignore file with rules for large files."""
    gitignore_content = """# Python
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
.venv/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/*.log
logs/

# Data - Raw (Large files, never commit)
data/raw/**/*.nii
data/raw/**/*.nii.gz
data/raw/**/*.csv
data/raw/**/*.zip
data/raw/**/*.tar
data/raw/**/*.gz

# Data - Processed (Large files)
data/processed/**/*.nii
data/processed/**/*.nii.gz
data/processed/**/*.csv

# Data - Analysis (Large results)
data/analysis/**/*.csv
data/analysis/**/*.json
data/analysis/**/*.pkl

# Outputs (Reports and Figures)
outputs/**/*.pdf
outputs/**/*.png
outputs/**/*.jpg
outputs/**/*.svg

# Environment Variables
.env
.env.local

# Temporary files
tmp/
temp/
*.tmp
"""
    gitignore_path = root_path / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    print(f"Created .gitignore at: {gitignore_path}")

def main():
    """Entry point for the directory setup script."""
    print("Setting up project directory structure...")
    ensure_directory_structure()
    print("Setup complete.")

if __name__ == "__main__":
    main()