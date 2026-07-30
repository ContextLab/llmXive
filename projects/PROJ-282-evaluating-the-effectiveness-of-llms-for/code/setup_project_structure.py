"""
Setup project structure for llmXive research pipeline.
Creates required directories: src/, tests/, data/, data/raw/, data/processed/, data/results/, state/
"""
import os
import sys
from pathlib import Path

def create_structure(project_root: Path = None):
    """
    Creates the standard project directory structure.
    
    Args:
        project_root: Path to the project root. Defaults to current directory.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    # Define required directories
    directories = [
        "src",
        "src/utils",
        "src/data",
        "src/models",
        "src/services",
        "src/analysis",
        "tests",
        "tests/unit",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "data/human_review",
        "state",
        "state/projects",
        "contracts",
        "figures"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    
    # Create placeholder __init__.py files
    init_files = [
        project_root / "src" / "__init__.py",
        project_root / "src" / "utils" / "__init__.py",
        project_root / "src" / "data" / "__init__.py",
        project_root / "src" / "models" / "__init__.py",
        project_root / "src" / "services" / "__init__.py",
        project_root / "src" / "analysis" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
    
    return True

if __name__ == "__main__":
    create_structure()
