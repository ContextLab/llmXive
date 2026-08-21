import os
import json
from pathlib import Path
from typing import List, Dict, Any
import datetime
from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error

def setup_project_directories():
    """
    T001 Helper: Creates the required directory structure.
    """
    project_root = get_path()
    
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
    logger = setup_logger("directory_manager")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            log_info(logger, f"Directory created: {full_path}")
        except Exception as e:
            log_error(logger, f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_paths

def initialize_checksums(created_paths: List[str]):
    """
    T001 Helper: Generates the structure_manifest.json.
    """
    project_root = get_path()
    manifest = {
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "project_root": str(project_root),
        "directories": created_paths,
        "count": len(created_paths)
    }
    
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / "structure_manifest.json"
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    log_info(setup_logger("directory_manager"), f"Manifest written to {manifest_path}")
    return manifest_path

def main():
    """
    Entry point for T001 execution.
    """
    try:
        created = setup_project_directories()
        initialize_checksums(created)
        return 0
    except Exception as e:
        log_error(setup_logger("directory_manager"), f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())