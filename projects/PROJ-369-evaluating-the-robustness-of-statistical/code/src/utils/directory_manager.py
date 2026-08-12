import os
import json
from pathlib import Path
from typing import List, Dict, Any
import datetime

from src.utils.config import get_path, ensure_dirs
from src.utils.logging import log_info, log_error, log_warning

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
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
    "state",
]

def setup_project_directories() -> List[str]:
    """
    Creates all required project directories.
    Returns a list of created paths relative to project root.
    """
    created_paths = []
    project_root = get_path("")

    for dir_name in REQUIRED_DIRS:
        full_path = Path(project_root) / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(dir_name)
            log_info(f"Directory created: {full_path}")
        except OSError as e:
            log_error(f"Failed to create directory {dir_name}: {e}")
            raise

    return created_paths

def initialize_checksums(created_paths: List[str]) -> Dict[str, Any]:
    """
    Creates the structure_manifest.json in the state/ directory.
    """
    project_root = get_path("")
    manifest = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project_root": str(project_root),
        "created_directories": created_paths,
        "verification_status": "completed",
        "manifest_version": "1.0"
    }

    manifest_path = Path(project_root) / "state" / "structure_manifest.json"
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        log_info(f"Structure manifest created at: {manifest_path}")
    except IOError as e:
        log_error(f"Failed to write structure manifest: {e}")
        raise

    return manifest

def main():
    """
    Entry point for script execution.
    """
    log_info("Starting project structure setup...")
    try:
        created = setup_project_directories()
        manifest = initialize_checksums(created)
        log_info("Project structure setup completed successfully.")
        return 0
    except Exception as e:
        log_error(f"Project structure setup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
