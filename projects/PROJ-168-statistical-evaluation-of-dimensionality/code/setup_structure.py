import os
from pathlib import Path

def create_project_structure():
    """
    Creates the directory structure for the project as specified in the implementation plan.
    Creates: projects/001-statistical-evaluation-of-dimensionality/{data/raw,data/processed,results,code,tests}
    """
    base_dir = Path("projects/001-statistical-evaluation-of-dimensionality")
    
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "results",
        base_dir / "code",
        base_dir / "tests"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py files to make directories proper Python packages where applicable
    (base_dir / "code" / "__init__.py").touch(exist_ok=True)
    (base_dir / "tests" / "__init__.py").touch(exist_ok=True)
    
    print(f"Project structure created successfully at {base_dir}")
    return True

if __name__ == "__main__":
    create_project_structure()
