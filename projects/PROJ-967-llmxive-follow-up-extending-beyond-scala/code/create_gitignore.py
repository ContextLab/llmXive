"""
Script to create the .gitignore file for the project.
This complements T001a by ensuring data directories are ignored.
"""
from pathlib import Path

GITIGNORE_CONTENT = """# Data files (large, versioned separately or ignored)
data/raw/
data/processed/

# Results and outputs
results/
figures/

# Python
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

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"""

def main() -> None:
    project_root = Path.cwd()
    gitignore_path = project_root / ".gitignore"
    
    if gitignore_path.exists():
        print(f"Warning: {gitignore_path} already exists. Overwriting.")
    
    gitignore_path.write_text(GITIGNORE_CONTENT)
    print(f"Created .gitignore at: {gitignore_path}")

if __name__ == "__main__":
    main()