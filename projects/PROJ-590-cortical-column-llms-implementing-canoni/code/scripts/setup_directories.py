import os
import sys
from pathlib import Path
import yaml
import datetime

# Define the project root relative to the script location or use CWD
# Assuming the script is run from the project root or code/ directory
def get_project_root():
    # If running as module or script, try to locate the project root
    # based on the presence of 'tasks.md' or 'specs'
    current = Path.cwd()
    while current != current.parent:
        if (current / "tasks.md").exists() or (current / "specs").exists():
            return current
        current = current.parent
    # Fallback to cwd if not found
    return Path.cwd()

def ensure_directory_structure(root: Path):
    """Create all required directories for the project."""
    dirs = [
        "src",
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "scripts",
        "data/results",
        "data/logs",
        "data/configs",
        "state",
    ]
    
    created = []
    for d in dirs:
        full_path = root / d
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it's a directory, not a file
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    return created

def create_state_template(root: Path):
    """Create state/template.yaml as a placeholder for versioning."""
    template_path = root / "state" / "template.yaml"
    if not template_path.exists():
        content = {
            "project": "PROJ-590-cortical-column-llms-implementing-canoni",
            "version": "0.0.1",
            "created_at": datetime.datetime.now().isoformat(),
            "status": "initialized",
            "checksums": {},
            "notes": "Initial state template. Update as artifacts are generated."
        }
        with open(template_path, "w") as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)
        return str(template_path)
    return None

def ensure_init_files(root: Path):
    """Create __init__.py in all src/ and tests/ directories."""
    init_dirs = [
        "src", "src/models", "src/data", "src/training", "src/experiments", "src/utils",
        "tests", "tests/unit", "tests/integration"
    ]
    created = []
    for d in init_dirs:
        dir_path = root / d
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created.append(str(init_file))
    return created

def create_gitignore(root: Path):
    """Create .gitignore excluding data/ except specific subdirs."""
    gitignore_path = root / ".gitignore"
    content = """# Python
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
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log

# Data (Exclude everything except configs, results, logs)
data/
!data/configs/
!data/results/
!data/logs/
data/*.npy
data/*.csv
data/*.json
data/*.yaml
data/*.pt
data/*.h5
data/*.parquet

# State (Track state files)
!state/

# OS
.DS_Store
Thumbs.db
"""
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write(content)
        return str(gitignore_path)
    return None

def main():
    root = get_project_root()
    print(f"Project root detected at: {root}")
    
    try:
        # 1. Create directories
        dirs = ensure_directory_structure(root)
        print(f"Created directories: {dirs}")
        
        # 2. Create state template
        state_file = create_state_template(root)
        if state_file:
            print(f"Created state template: {state_file}")
        else:
            print("State template already exists.")
        
        # 3. Create __init__.py files
        inits = ensure_init_files(root)
        print(f"Created __init__.py files: {inits}")
        
        # 4. Create .gitignore
        gitignore = create_gitignore(root)
        if gitignore:
            print(f"Created .gitignore: {gitignore}")
        else:
            print(".gitignore already exists.")
        
        print("Setup completed successfully.")
        return 0
    except Exception as e:
        print(f"Setup failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())