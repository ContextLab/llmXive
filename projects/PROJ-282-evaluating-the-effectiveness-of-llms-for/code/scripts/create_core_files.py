"""
Script to create core project files: __init__.py, .gitignore, and requirements.txt.
Generates a verification log at data/logs/core_files.json.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

# Import shared utilities from the project structure
# Note: Using relative import style compatible with the project's src layout
# If executed as a script, we adjust sys.path
def ensure_init_files(root_dir: Path) -> List[Dict[str, Any]]:
    """
    Creates __init__.py in all subdirectories under root_dir (specifically src/).
    Returns a list of created file info dicts.
    """
    created = []
    src_dir = root_dir / "src"
    if not src_dir.exists():
        # Fallback if src doesn't exist yet, create it first
        src_dir.mkdir(parents=True, exist_ok=True)
    
    # Walk the src directory to find all directories
    for dirpath, dirnames, filenames in os.walk(src_dir):
        # Create __init__.py if it doesn't exist
        init_path = Path(dirpath) / "__init__.py"
        if not init_path.exists():
            # Write a standard docstring
            init_path.write_text('"""Auto-generated package initialization."""\n')
            created.append({
                "path": str(init_path.relative_to(root_dir)),
                "action": "created"
            })
        else:
            # Check if we should update it (optional, but good practice)
            # For this task, we just note existence
            created.append({
                "path": str(init_path.relative_to(root_dir)),
                "action": "exists"
            })
    
    return created

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_gitignore(root_dir: Path) -> Dict[str, Any]:
    """
    Creates a .gitignore file if it doesn't exist.
    Returns file info dict.
    """
    gitignore_path = root_dir / ".gitignore"
    if gitignore_path.exists():
        return {
            "path": str(gitignore_path.relative_to(root_dir)),
            "action": "exists",
            "checksum": compute_sha256(gitignore_path)
        }
    
    content = """
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

# Virtual Environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/raw/
data/processed/
data/results/
data/logs/
state/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
"""
    gitignore_path.write_text(content.strip())
    return {
        "path": str(gitignore_path.relative_to(root_dir)),
        "action": "created",
        "checksum": compute_sha256(gitignore_path)
    }

def create_requirements(root_dir: Path) -> Dict[str, Any]:
    """
    Creates requirements.txt if it doesn't exist.
    Returns file info dict.
    """
    req_path = root_dir / "requirements.txt"
    if req_path.exists():
        return {
            "path": str(req_path.relative_to(root_dir)),
            "action": "exists",
            "checksum": compute_sha256(req_path)
        }
    
    # Based on T002 prerequisites
    content = """transformers
scikit-learn
pandas
tree-sitter
networkx
requests
pyyaml
bitsandbytes
sentence-transformers
pytest
radon
statsmodels
pydantic
"""
    req_path.write_text(content)
    return {
        "path": str(req_path.relative_to(root_dir)),
        "action": "created",
        "checksum": compute_sha256(req_path)
    }

def main():
    """Main entry point for creating core files."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    print(f"Project root detected at: {project_root}")
    
    # 1. Ensure __init__.py files
    init_results = ensure_init_files(project_root)
    
    # 2. Create .gitignore
    gitignore_result = create_gitignore(project_root)
    
    # 3. Create requirements.txt
    requirements_result = create_requirements(project_root)
    
    # Compile results
    all_files = []
    
    # Add init files
    for item in init_results:
        full_path = project_root / item["path"]
        all_files.append({
            "path": item["path"],
            "action": item["action"],
            "checksum": compute_sha256(full_path)
        })
    
    all_files.append(gitignore_result)
    all_files.append(requirements_result)
    
    # Create output directory
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Write verification log
    output_path = logs_dir / "core_files.json"
    output_data = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "total_files": len(all_files),
        "files": all_files
    }
    
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Core files verification log written to: {output_path}")
    print(f"Total files processed: {len(all_files)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())