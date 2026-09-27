#!/usr/bin/env python3
"""
verify_structure.py - Verify that all required project directories exist.
Exits with code 1 if any required path is missing.
Generates project_structure.log with verification results.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def verify_structure(project_root: str) -> bool:
    """
    Verify all required directories exist under project_root.
    Returns True if all exist, False otherwise.
    """
    required_paths = [
        "code",
        "tests",
        "data",
        "docs",
        "scripts",
        "results",
        "specs/001-entropy-validity-prediction/contracts",
        "code/src",
        "code/data/raw",
        "code/data/processed",
        "code/artifacts",
        "code/state",
        "code/logs",
        "code/src/utils",
        "code/src/data",
        "code/src/generation",
        "code/src/analysis",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
    ]

    project_path = Path(project_root)
    missing_paths = []

    for rel_path in required_paths:
        full_path = project_path / rel_path
        if not full_path.exists():
            missing_paths.append(str(full_path))
        elif not full_path.is_dir():
            missing_paths.append(f"{full_path} (exists but is not a directory)")

    if missing_paths:
        print("ERROR: Missing or invalid paths:")
        for path in missing_paths:
            print(f"  - {path}")
        return False

    print("All required directories exist.")
    return True

def write_log(project_root: str, success: bool, missing_paths: list = None):
    """Write verification results to project_structure.log"""
    log_path = Path(project_root).parent / "project_structure.log"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_root": project_root,
        "success": success,
        "missing_paths": missing_paths or []
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: verify_structure.py <project_root>")
        sys.exit(1)

    project_root = sys.argv[1]
    
    if not Path(project_root).exists():
        print(f"ERROR: Project root does not exist: {project_root}")
        write_log(project_root, False, [project_root])
        sys.exit(1)

    success = verify_structure(project_root)
    
    if success:
        write_log(project_root, True)
        sys.exit(0)
    else:
        write_log(project_root, False)
        sys.exit(1)

if __name__ == "__main__":
    main()