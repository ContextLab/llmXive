import os
import sys
from pathlib import Path
import json
from datetime import datetime
from src.utils.config import get_path, ensure_dirs

def main():
    """
    T001: Create project structure and generate structure_manifest.json.
    """
    project_root = get_path()
    
    # Define all required directories relative to project root
    required_dirs = [
        "src",
        "src/data",
        "src/synthesis",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "state"
    ]
    
    created_paths = []
    
    print(f"Project Root: {project_root}")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            print(f"Created: {full_path}")
        except Exception as e:
            print(f"Error creating {full_path}: {e}")
            return 1
    
    # Generate the manifest
    manifest = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(project_root),
        "directories": created_paths,
        "count": len(created_paths)
    }
    
    manifest_path = project_root / "state" / "structure_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to: {manifest_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
