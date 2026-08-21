import os
import json
from pathlib import Path
from typing import List, Dict, Any
import datetime
from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error

def setup_project_directories():
    """
    T001 Implementation Helper: Creates the required directory structure.
    
    Returns a list of created paths.
    """
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

    project_root = get_path()
    created_paths = []
    logger = setup_logger("directory_manager")

    log_info(logger, f"Setting up project structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = Path(project_root) / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(full_path))
                log_info(logger, f"Created directory: {full_path}")
            else:
                created_paths.append(str(full_path))
                log_info(logger, f"Directory exists: {full_path}")
        except Exception as e:
            log_error(logger, f"Failed to create {full_path}: {str(e)}")
            raise
    
    return created_paths

def initialize_checksums(created_paths: List[str]):
    """
    T001 Implementation Helper: Initializes the structure manifest.
    
    Creates state/structure_manifest.json with the list of created paths.
    """
    project_root = get_path()
    manifest_path = Path(project_root) / "state" / "structure_manifest.json"
    
    ensure_dirs([str(Path(project_root) / "state")])

    manifest = {
        "created_at": datetime.datetime.now().isoformat(),
        "project_root": str(project_root),
        "directories_created": created_paths,
        "total_count": len(created_paths),
        "errors": [],
        "status": "success"
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    log_info(None, f"Structure manifest written to: {manifest_path}")
    return manifest_path

def main():
    """Entry point for directory setup script."""
    created = setup_project_directories()
    manifest = initialize_checksums(created)
    print(f"Project structure ready. Manifest: {manifest}")

if __name__ == "__main__":
    main()