import os
from pathlib import Path
from typing import List, Dict, Any
import json
import datetime
from src.utils.config import get_path, ensure_dirs
from src.utils.logging import setup_logger, log_info, log_error, log_warning

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
    Returns a list of paths that were created.
    """
    project_root = get_path("")
    created_paths = []

    logger = setup_logger("directory_manager")

    for dir_name in REQUIRED_DIRS:
        target_path = Path(project_root) / dir_name
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(target_path))
            log_info(logger, f"Created directory: {target_path}")
        except Exception as e:
            log_error(logger, f"Failed to create directory {target_path}: {e}")
            raise

    return created_paths

def initialize_checksums(created_paths: List[str]) -> Dict[str, Any]:
    """
    Generates the structure manifest JSON listing all created paths.
    """
    manifest = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project_root": str(get_path("")),
        "directories": created_paths,
        "status": "complete",
    }

    manifest_path = Path(get_path("state")) / "structure_manifest.json"
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        log_info(None, f"Manifest written to {manifest_path}")
    except Exception as e:
        log_error(None, f"Failed to write manifest: {e}")
        raise

    return manifest

def main() -> int:
    """
    Entry point for the setup script.
    """
    logger = setup_logger("directory_manager")
    try:
        log_info(logger, "Starting project directory setup...")
        created = setup_project_directories()
        manifest = initialize_checksums(created)
        log_info(logger, f"Setup complete. Created {len(created)} directories.")
        log_info(logger, f"Manifest: {json.dumps(manifest, indent=2)}")
        return 0
    except Exception as e:
        log_error(logger, f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
