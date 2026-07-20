"""
Setup script to create the project directory structure.
This script ensures all required directories exist for the llmXive project.
"""
import os
from pathlib import Path

def main():
    # Define the project root
    project_root = Path("projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c")
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs",
        "results",
        "config",
        "specs/contracts"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Ensure code/__init__.py exists (though it should be managed by version control,
    # we create it here if missing to ensure the package is importable immediately)
    init_file = project_root / "code" / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created empty file: {init_file}")
    else:
        print(f"File already exists: {init_file}")
    
    print("Project directory structure setup complete.")

if __name__ == "__main__":
    main()