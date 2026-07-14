"""
Script to create the project directory structure and placeholder files.
This satisfies T001: Create project structure.
"""
import os
from pathlib import Path

def setup_project_structure():
    """Create required directories and placeholder files."""
    root = Path(".")
    
    # Define directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "state",
        "logs",
        "figures",
        "data/text",
        "data/neural",
        "data/neural/processed",
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    # (even if empty, git needs a file to track the directory)
    data_dirs = ["data/raw", "data/processed", "data/results", "data/text", "data/neural/processed"]
    for data_dir in data_dirs:
        keep_file = root / data_dir / ".gitkeep"
        if not keep_file.exists():
            keep_file.touch()
            print(f"Created placeholder: {keep_file}")
    
    # Create __init__.py in code directory if not exists
    code_init = root / "code" / "__init__.py"
    if not code_init.exists():
        code_init.write_text('"""Neural Narrative Networks Research Pipeline."""\n')
        print(f"Created: {code_init}")
    
    # Create .gitignore if not exists
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
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

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
.tox/
.nox/

# Virtual environments
.venv/
venv/
ENV/
env/
.env/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# OS
.DS_Store
Thumbs.db

# Project specific
data/raw/
!data/raw/.gitkeep
data/processed/
!data/processed/.gitkeep
data/results/
!data/results/.gitkeep
logs/
state/
figures/
"""
        gitignore.write_text(gitignore_content)
        print(f"Created: {gitignore}")
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    setup_project_structure()