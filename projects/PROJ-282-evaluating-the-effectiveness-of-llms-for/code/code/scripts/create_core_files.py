"""
Script to create core __init__.py files, .gitignore, and requirements.txt,
then generate a verification log at data/logs/core_files.json.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this script (assuming script is in code/scripts)
# We need to go up two levels to reach 'code' which is the project root in this context
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_init_files(base_dir: Path, subdirs: List[str]):
    """Create __init__.py in base and all subdirectories."""
    created_files = []
    for subdir in subdirs:
        target_dir = base_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        init_file = target_dir / "__init__.py"
        if not init_file.exists():
            # Create a minimal comment to identify the package
            init_file.write_text(f"# Package: {subdir}\n", encoding="utf-8")
        created_files.append(init_file)
    return created_files

def create_gitignore(root: Path) -> Path:
    """Create .gitignore if it doesn't exist."""
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
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

# OS
.DS_Store
Thumbs.db

# Project specific
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
data/results/*
!data/results/.gitkeep
state/*
!state/.gitkeep
data/logs/*.json
!data/logs/.gitkeep
*.log
.coverage
htmlcov/
.mypy_cache/

# Secrets
.env
*.pem
*.key
"""
        gitignore_path.write_text(content, encoding="utf-8")
    return gitignore_path

def create_requirements(root: Path) -> Path:
    """Create requirements.txt if it doesn't exist."""
    req_path = root / "requirements.txt"
    if not req_path.exists():
        content = """transformers>=4.30.0
scikit-learn>=1.2.0
pandas>=2.0.0
tree-sitter>=0.20.0
networkx>=3.0.0
requests>=2.28.0
pyyaml>=6.0.0
bitsandbytes>=0.39.0
sentence-transformers>=2.2.0
pytest>=7.0.0
radon>=6.0.0
statsmodels>=0.14.0
pydantic>=2.0.0
ruff>=0.1.0
black>=23.0.0
pre-commit>=3.0.0
pyarrow>=12.0.0
tqdm>=4.65.0
psutil>=5.9.0
"""
        req_path.write_text(content, encoding="utf-8")
    return req_path

def main():
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Define directory structure to initialize
    src_dirs = [
        "src", "src/utils", "src/data", "src/models", "src/analysis",
        "tests", "tests/unit",
        "data", "data/raw", "data/processed", "data/results", "data/logs",
        "state", "contracts"
    ]

    created_files: List[Dict[str, Any]] = []

    # 1. Create __init__.py files
    for subdir in src_dirs:
        target_dir = PROJECT_ROOT / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        init_file = target_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# Package: {subdir}\n", encoding="utf-8")
        created_files.append({
            "path": str(init_file.relative_to(PROJECT_ROOT)),
            "checksum": compute_sha256(init_file),
            "size_bytes": init_file.stat().st_size
        })

    # 2. Create .gitignore
    gitignore = create_gitignore(PROJECT_ROOT)
    created_files.append({
        "path": str(gitignore.relative_to(PROJECT_ROOT)),
        "checksum": compute_sha256(gitignore),
        "size_bytes": gitignore.stat().st_size
    })

    # 3. Create requirements.txt
    requirements = create_requirements(PROJECT_ROOT)
    created_files.append({
        "path": str(requirements.relative_to(PROJECT_ROOT)),
        "checksum": compute_sha256(requirements),
        "size_bytes": requirements.stat().st_size
    })

    # 4. Generate verification log
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "core_files.json"

    report = {
        "task_id": "T001b",
        "timestamp": None, # Will be set by execution if needed, or left null for static
        "project_root": str(PROJECT_ROOT),
        "files_created_or_verified": created_files,
        "total_files": len(created_files)
    }

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Core files verification log written to: {log_path}")
    print(f"Total files processed: {len(created_files)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())