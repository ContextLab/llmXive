import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def create_structure(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Creates the required project directory structure and necessary files.
    
    Returns a dictionary containing:
    - 'created_dirs': list of created directory paths
    - 'created_files': list of created file paths
    - 'errors': list of error messages if any
    """
    if base_path is None:
        base_path = Path.cwd()
    
    created_dirs = []
    created_files = []
    errors = []
    
    # Define required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state"
    ]
    
    # Create directories
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except Exception as e:
            errors.append(f"Failed to create directory {dir_path}: {str(e)}")
    
    # Create .gitkeep files in data directories
    data_dirs = ["data/raw", "data/processed"]
    for dir_path in data_dirs:
        full_path = base_path / dir_path / ".gitkeep"
        try:
            full_path.touch(exist_ok=True)
            created_files.append(str(full_path))
        except Exception as e:
            errors.append(f"Failed to create .gitkeep in {dir_path}: {str(e)}")
    
    # Create .gitignore file
    gitignore_path = base_path / ".gitignore"
    gitignore_content = """# Data directories
data/raw/*
data/processed/*

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Model caches
data/models/*
!data/models/.gitkeep

# Environment files
.env
.env.local

# IDE and editor files
.idea/
.vscode/
*.swp
*.swo
*~

# Jupyter notebooks
.ipynb_checkpoints/

# Logs
*.log
"""
    try:
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        created_files.append(str(gitignore_path))
    except Exception as e:
        errors.append(f"Failed to create .gitignore: {str(e)}")
    
    # Create .gitkeep in root code and tests directories to ensure they are tracked
    root_code_gitkeep = base_path / "code" / ".gitkeep"
    root_tests_gitkeep = base_path / "tests" / ".gitkeep"
    
    try:
        root_code_gitkeep.touch(exist_ok=True)
        created_files.append(str(root_code_gitkeep))
    except Exception as e:
        errors.append(f"Failed to create code/.gitkeep: {str(e)}")
    
    try:
        root_tests_gitkeep.touch(exist_ok=True)
        created_files.append(str(root_tests_gitkeep))
    except Exception as e:
        errors.append(f"Failed to create tests/.gitkeep: {str(e)}")
    
    return {
        "created_dirs": created_dirs,
        "created_files": created_files,
        "errors": errors
    }

def main():
    """Main entry point for creating project structure."""
    base_path = Path.cwd()
    print(f"Creating project structure in: {base_path}")
    
    result = create_structure(base_path)
    
    if result["errors"]:
        print("Errors encountered:")
        for error in result["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    
    print(f"Successfully created {len(result['created_dirs'])} directories:")
    for dir_path in result["created_dirs"]:
        print(f"  - {dir_path}")
    
    print(f"Successfully created {len(result['created_files'])} files:")
    for file_path in result["created_files"]:
        print(f"  - {file_path}")
    
    print("\nProject structure created successfully!")

if __name__ == "__main__":
    main()