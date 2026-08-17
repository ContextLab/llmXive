import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

# Constants for project structure based on plan.md
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIRS = [
    "src/utils",
    "src/models",
    "src/data",
    "src/analysis",
    "src/scripts",
]
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "data/logs",
    "data/human_review",
]
TEST_DIRS = [
    "tests/unit",
    "tests/integration",
]
CONTRACTS_DIR = "contracts"
STATE_DIR = "state/projects"

GITIGNORE_CONTENT = """# Python
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
.venv

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Data (Raw and Intermediate - keep processed/results only in git if small)
data/raw/**
!data/raw/.gitkeep
data/processed/*.parquet
data/processed/*.csv
data/results/*.json
data/results/*.csv
data/results/*.png
data/logs/*.json

# State
state/**/*.yaml
!state/projects/.gitkeep

# Logs
*.log

# OS
.DS_Store
Thumbs.db
"""

REQUIREMENTS_CONTENT = """# Core ML & Data Processing
transformers>=4.35.0
scikit-learn>=1.3.0
pandas>=2.0.0
torch>=2.0.0
numpy>=1.24.0
sentence-transformers>=2.2.0
bitsandbytes>=0.41.0

# Data Ingestion & Processing
datasets>=2.14.0
pyarrow>=12.0.0
requests>=2.31.0

# Static Analysis & Code Parsing
tree-sitter>=0.20.0
radon>=6.0.0

# Statistical Analysis
statsmodels>=0.14.0
scipy>=1.11.0

# Configuration & Logging
pyyaml>=6.0.0

# Testing
pytest>=7.4.0

# Utilities
tqdm>=4.66.0
"""

def get_project_root() -> Path:
    return PROJECT_ROOT

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def ensure_init_files() -> List[Dict[str, Any]]:
    """Create __init__.py in all specified subdirectories."""
    created_files = []
    root = get_project_root()
    
    all_dirs = SRC_DIRS + DATA_DIRS + TEST_DIRS + [CONTRACTS_DIR, STATE_DIR]
    
    for dir_path in all_dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_files.append({
                "path": str(init_file.relative_to(root)),
                "type": "init",
                "checksum": compute_sha256(init_file)
            })
        else:
            # Still record existing init files for completeness
            created_files.append({
                "path": str(init_file.relative_to(root)),
                "type": "init",
                "checksum": compute_sha256(init_file),
                "status": "existed"
            })
    
    return created_files

def create_gitignore() -> Dict[str, Any]:
    """Create .gitignore file at project root."""
    root = get_project_root()
    gitignore_path = root / ".gitignore"
    
    with open(gitignore_path, "w") as f:
        f.write(GITIGNORE_CONTENT)
    
    return {
        "path": str(gitignore_path.relative_to(root)),
        "type": "gitignore",
        "checksum": compute_sha256(gitignore_path)
    }

def create_requirements() -> Dict[str, Any]:
    """Create requirements.txt file at project root."""
    root = get_project_root()
    req_path = root / "requirements.txt"
    
    with open(req_path, "w") as f:
        f.write(REQUIREMENTS_CONTENT)
    
    return {
        "path": str(req_path.relative_to(root)),
        "type": "requirements",
        "checksum": compute_sha256(req_path)
    }

def main():
    """Main entry point to create core files and generate verification log."""
    print("Starting core file creation...")
    
    root = get_project_root()
    print(f"Project root: {root}")
    
    # Ensure directory structure exists
    all_dirs = SRC_DIRS + DATA_DIRS + TEST_DIRS + [CONTRACTS_DIR, STATE_DIR]
    for dir_path in all_dirs:
        (root / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    init_files = ensure_init_files()
    print(f"Created/verified {len(init_files)} __init__.py files")
    
    # Create .gitignore
    gitignore_info = create_gitignore()
    print(f"Created {gitignore_info['path']}")
    
    # Create requirements.txt
    requirements_info = create_requirements()
    print(f"Created {requirements_info['path']}")
    
    # Compile all created files info
    all_files = init_files + [gitignore_info, requirements_info]
    
    # Generate verification log
    log_entry = {
        "task_id": "T001b",
        "timestamp": str(Path(root).stat().st_mtime), # Using mtime as proxy for run time in this context
        "created_files": all_files,
        "summary": {
            "total_files": len(all_files),
            "init_files": len(init_files),
            "config_files": 2
        }
    }
    
    # Write verification log
    log_path = root / "data" / "logs" / "core_files.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2)
    
    print(f"Verification log written to {log_path}")
    print("Core file creation complete.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())