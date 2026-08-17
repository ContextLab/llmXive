import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

# Ensure we can import from the project root if run as a module
# This script is located at code/code/scripts/create_core_files.py
# The project root is likely code/ or code/code/ depending on structure.
# We will assume the script is run from the project root or code/ directory.
# We will use the existing `src` structure defined in T001a.

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Based on T001a, the structure is created under a root.
    We assume the script is run from the directory containing 'src', 'data', etc.
    """
    current = Path.cwd()
    # Check if we are in the root or one level deep (e.g., code/)
    # Standard convention: root has src/, data/, tests/
    if (current / "src").exists() and (current / "data").exists():
        return current
    if (current / "code").exists() and (current / "code" / "src").exists():
        return current / "code"
    # Fallback: assume current is root
    return current

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"

def ensure_init_files(src_root: Path) -> List[Dict[str, Any]]:
    """
    Create __init__.py in all subdirectories under src_root.
    Returns a list of created files with metadata.
    """
    created_files = []
    if not src_root.exists():
        return created_files

    # Walk through all directories under src_root
    for dirpath, dirnames, filenames in os.walk(src_root):
        # Skip hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        
        # Check if __init__.py already exists
        init_file = Path(dirpath) / "__init__.py"
        if not init_file.exists():
            # Create __init__.py with a standard docstring
            init_file.write_text(
                "# Auto-generated __init__.py\n"
                f"# Created by T001b on {Path.cwd().name}\n"
                "__path__ = __import__('pkgutil').extend_path(__path__, __name__)\n"
            )
            created_files.append({
                "path": str(init_file.relative_to(src_root.parent)),
                "type": "init",
                "status": "created"
            })
        else:
            # Even if exists, we might want to log it for the report
            created_files.append({
                "path": str(init_file.relative_to(src_root.parent)),
                "type": "init",
                "status": "exists"
            })
    return created_files

def create_gitignore(root: Path) -> Dict[str, Any]:
    """Create .gitignore if it doesn't exist."""
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        return {
            "path": str(gitignore_path),
            "status": "exists",
            "checksum": compute_sha256(gitignore_path)
        }

    content = (
        "# Python\n"
        "__pycache__/\n"
        "*.py[cod]\n"
        "*$py.class\n"
        ".eggs/\n"
        "*.egg-info/\n"
        ".pytest_cache/\n"
        ".mypy_cache/\n"
        ".coverage\n"
        "htmlcov/\n"
        "\n"
        "# Virtual Environments\n"
        "venv/\n"
        "env/\n"
        ".venv/\n"
        "\n"
        "# IDE\n"
        ".idea/\n"
        ".vscode/\n"
        "*.swp\n"
        "*.swo\n"
        "\n"
        "# OS\n"
        ".DS_Store\n"
        "Thumbs.db\n"
        "\n"
        "# Data (Raw and Processed - large files)\n"
        "data/raw/*\n"
        "!data/raw/.gitkeep\n"
        "data/processed/*\n"
        "!data/processed/.gitkeep\n"
        "\n"
        "# Logs\n"
        "data/logs/*\n"
        "!data/logs/.gitkeep\n"
        "\n"
        "# Results\n"
        "data/results/*\n"
        "!data/results/.gitkeep\n"
        "\n"
        "# Models (Large binaries)\n"
        "models/\n"
        "*.bin\n"
        "*.pt\n"
        "*.pth\n"
    )
    gitignore_path.write_text(content)
    return {
        "path": str(gitignore_path),
        "status": "created",
        "checksum": compute_sha256(gitignore_path)
    }

def create_requirements(root: Path) -> Dict[str, Any]:
    """Create requirements.txt if it doesn't exist."""
    req_path = root / "requirements.txt"
    
    # Check if T002 already created it (often in root)
    if req_path.exists():
       return {
           "path": str(req_path),
           "status": "exists",
           "checksum": compute_sha256(req_path)
       }

    # T002 lists specific dependencies. We create a standard one if missing.
    content = (
        "# Core Data & ML\n"
        "transformers>=4.30.0\n"
        "torch>=2.0.0\n"
        "scikit-learn>=1.3.0\n"
        "pandas>=2.0.0\n"
        "pyarrow>=12.0.0\n"
        "\n"
        "# Code Analysis\n"
        "tree-sitter>=0.20.0\n"
        "tree-sitter-languages>=1.8.0\n"
        "radon>=6.0.0\n"
        "networkx>=3.0.0\n"
        "\n"
        "# Utilities\n"
        "requests>=2.31.0\n"
        "pyyaml>=6.0.0\n"
        "\n"
        "# LLM Specific\n"
        "bitsandbytes>=0.39.0\n"
        "sentence-transformers>=2.2.0\n"
        "\n"
        "# Testing & Linting\n"
        "pytest>=7.3.0\n"
        "ruff>=0.0.280\n"
        "black>=23.0.0\n"
        "\n"
        "# Statistics\n"
        "statsmodels>=0.14.0\n"
    )
    req_path.write_text(content)
    return {
        "path": str(req_path),
        "status": "created",
        "checksum": compute_sha256(req_path)
    }

def main():
    """
    Main execution for T001b: Create Core Files.
    1. Ensure __init__.py in all src/ subdirectories.
    2. Create .gitignore.
    3. Create requirements.txt.
    4. Generate data/logs/core_files.json with checksums.
    """
    root = get_project_root()
    src_root = root / "src"
    logs_dir = root / "data" / "logs"
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # 1. Create __init__.py files
    if src_root.exists():
        init_results = ensure_init_files(src_root)
        for item in init_results:
            # Compute checksum for created/updated files
            full_path = root / item["path"]
            if full_path.exists():
                item["checksum"] = compute_sha256(full_path)
            results.append(item)
    
    # 2. Create .gitignore
    gitignore_info = create_gitignore(root)
    results.append(gitignore_info)
    
    # 3. Create requirements.txt
    req_info = create_requirements(root)
    results.append(req_info)
    
    # 4. Write core_files.json
    output_file = logs_dir / "core_files.json"
    report = {
        "task_id": "T001b",
        "timestamp": str(Path.cwd().name), # Placeholder for actual timestamp if needed
        "root": str(root),
        "files": results
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"Core files verification written to: {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
