import os
import sys
from pathlib import Path

def create_structure():
    """
    Create the project directory structure for PROJ-062.
    This implements T001: Create project structure per implementation plan.
    
    Structure created:
    - projects/PROJ-062-quantifying-the-impact-of-code-ownership/
      - code/
        - utils/
        - scripts/
      - data/
        - raw/
        - intermediate/
        - results/
      - specs/
      - tests/
        - unit/
        - integration/
      - figures/
      - state/
      - requirements.txt
      - .gitignore
    """
    base_dir = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
    
    # Define all directories to create
    directories = [
        base_dir / "code" / "utils",
        base_dir / "code" / "scripts",
        base_dir / "data" / "raw",
        base_dir / "data" / "intermediate",
        base_dir / "data" / "results",
        base_dir / "specs",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "integration",
        base_dir / "figures",
        base_dir / "state",
    ]
    
    # Create directories
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Add .gitkeep to data directories to ensure they are tracked
        if dir_path.parts[0] == "data":
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
    
    # Create requirements.txt
    req_file = base_dir / "requirements.txt"
    if not req_file.exists():
        req_content = """GitPython
scikit-learn
scipy
pandas
numpy
radon
matplotlib
pyyaml
requests
pytest
"""
        req_file.write_text(req_content)
    
    # Create .gitignore
    gitignore_file = base_dir / ".gitignore"
    if not gitignore_file.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Data
data/raw/*
data/intermediate/*
!data/raw/.gitkeep
!data/intermediate/.gitkeep

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
"""
        gitignore_file.write_text(gitignore_content)
    
    # Create __init__.py files to make directories packages
    init_files = [
        base_dir / "code" / "__init__.py",
        base_dir / "code" / "utils" / "__init__.py",
        base_dir / "code" / "scripts" / "__init__.py",
        base_dir / "tests" / "__init__.py",
        base_dir / "tests" / "unit" / "__init__.py",
        base_dir / "tests" / "integration" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
    
    print(f"Project structure created at: {base_dir}")
    return base_dir

def main():
    create_structure()

if __name__ == "__main__":
    main()