"""
Project structure initialization.

Sets up the basic file structure and configuration files
required for the project.
"""
import os
from pathlib import Path

def main():
    """
    Initialize project structure.
    
    Creates:
    - Basic directory structure
    - __init__.py files
    - .gitkeep files for empty directories
    """
    project_root = Path(__file__).parent.parent
    
    # Ensure code directory has __init__.py
    code_dir = project_root / "code"
    init_file = code_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Initialization file for the code package."""\n')
        print(f"Created {init_file}")
    
    # Create .gitkeep in root directories
    root_dirs = ["code", "tests", "data", "artifacts"]
    for dir_name in root_dirs:
        dir_path = project_root / dir_name
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in {dir_name}/")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
