"""
Project Structure Setup Script for llmXive Mesh Network Supercomputer.

This script creates the required directory structure and initializes
all necessary __init__.py files and configuration files.
"""
import os
from pathlib import Path
from typing import List

# Define the required directory structure
REQUIRED_DIRS: List[str] = [
    "code/orchestrator",
    "code/analysis",
    "code/simulation",
    "code/data/raw",
    "code/data/processed",
    "code/tests/unit",
    "code/tests/integration",
    "code/tests/contract",
]

# Define the .gitignore content
GITIGNORE_CONTENT: str = """# Data directories
data/
code/data/

# Logs
*.log

# Python cache
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

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Jupyter Notebook
.ipynb_checkpoints

# Environment variables
.env
.env.local

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""

def create_structure(base_path: Path = None) -> None:
    """
    Create the project directory structure and required files.
    
    Args:
        base_path: Base directory for the project. Defaults to current directory.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    print(f"Creating project structure in: {base_path}")
    
    # Create all required directories
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {full_path}")
        
        # Create __init__.py in each directory
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""{dir_path} module."""\n')
            print(f"    Created: {init_file}")
        else:
            print(f"    Already exists: {init_file}")
    
    # Create .gitignore at project root
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(GITIGNORE_CONTENT)
        print(f"Created: {gitignore_path}")
    else:
        print(f".gitignore already exists at: {gitignore_path}")
    
    print("Project structure setup complete.")

def main() -> None:
    """Main entry point for the setup script."""
    create_structure()

if __name__ == "__main__":
    main()