"""
Script to create the project directory structure for llmXive follow-up.
This script creates the required directories as specified in the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the full project directory structure."""
    # Define the project root
    project_root = Path("projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc")
    
    # Define all required directories
    directories = [
        # Code modules
        project_root / "code" / "gatekeeper",
        project_root / "code" / "metrics",
        project_root / "code" / "analysis",
        project_root / "code" / "data",
        
        # Data directories
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        
        # Test directories
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        
        # Other directories
        project_root / "paper",
        project_root / "scripts",
        
        # Additional standard directories
        project_root / "specs",
        project_root / "config",
    ]
    
    # Create all directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {directory}")
        else:
            print(f"Already exists: {directory}")
    
    # Create __init__.py files for Python packages
    package_dirs = [
        project_root / "code" / "gatekeeper",
        project_root / "code" / "metrics",
        project_root / "code" / "analysis",
        project_root / "code" / "data",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]
    
    for package_dir in package_dirs:
        init_file = package_dir / "__init__.py"
        if not init_file.exists():
          init_file.touch()
          print(f"Created: {init_file}")
    
    print(f"\nProject structure created successfully!")
    print(f"Total directories created: {created_count}")
    print(f"Project root: {project_root.resolve()}")
    
    # List created structure
    print("\nDirectory structure:")
    for root, dirs, files in os.walk(project_root):
        level = root.replace(str(project_root), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{subindent}{file}')

if __name__ == "__main__":
    create_project_structure()
