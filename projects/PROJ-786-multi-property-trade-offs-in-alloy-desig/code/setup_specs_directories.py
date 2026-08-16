import os
from pathlib import Path

def create_specs_directories():
    """
    Creates the directory structure for specifications as required by T001e.
    Specifically creates: projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/specs/001-multi-property-trade-offs/
    Also ensures parent directories exist.
    """
    project_root = Path.cwd()
    
    # Define the target path relative to project root
    specs_dir = project_root / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig" / "specs" / "001-multi-property-trade-offs"
    
    # Create the directory structure (parents=True ensures all intermediate dirs are created)
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep in the new directory to ensure it is tracked by git
    gitkeep_path = specs_dir / ".gitkeep"
    gitkeep_path.touch()
    
    print(f"Created directory structure: {specs_dir}")
    print(f"Created placeholder file: {gitkeep_path}")
    
    return True

if __name__ == "__main__":
    create_specs_directories()
