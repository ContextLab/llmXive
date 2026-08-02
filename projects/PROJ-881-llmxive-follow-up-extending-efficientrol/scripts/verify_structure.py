#!/usr/bin/env python3
"""
Verify that all project directories created by T004a (setup.sh) exist.

This script checks the directory structure defined in the project plan
and generates a JSON log file with the verification results.
"""
import json
import os
import sys
from pathlib import Path

# Define the expected directory structure relative to the project root
# These paths match the mkdir -p commands from T004a setup.sh
EXPECTED_DIRS = [
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/tests/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/data/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/docs/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/scripts/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/results/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/specs/001-entropy-validity-prediction/contracts/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/src/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/data/raw/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/data/processed/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/artifacts/",
    "projects/PROJ-881-llmxive-follow-up-extending-efficientrol/code/state/",
]

def verify_structure(root_path: Path) -> list:
    """
    Verify that all expected directories exist under root_path.
    
    Args:
        root_path: The root directory of the project.
        
    Returns:
        A list of dictionaries with 'path' and 'exists' keys.
    """
    results = []
    for dir_path in EXPECTED_DIRS:
        full_path = root_path / dir_path
        exists = full_path.is_dir()
        results.append({
            "path": str(full_path.absolute()),
            "exists": exists
        })
    return results

def main():
    """Main entry point for the verification script."""
    # Determine the project root (parent of the scripts directory)
    # Assuming this script is located at: projects/PROJ-881-.../scripts/verify_structure.py
    script_path = Path(__file__).resolve()
    current_dir = script_path.parent
    project_root = current_dir.parent  # Go up one level to the project root

    print(f"Verifying project structure at: {project_root}")
    
    # Verify structure
    results = verify_structure(project_root)
    
    # Check if all directories exist
    all_exist = all(item["exists"] for item in results)
    
    # Generate log file
    log_file = project_root / "project_structure.log"
    log_data = {"paths": results}
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    
    print(f"Verification log written to: {log_file}")
    
    # Print summary
    missing = [item["path"] for item in results if not item["exists"]]
    if missing:
        print(f"\n❌ Missing directories ({len(missing)}):")
        for path in missing:
            print(f"  - {path}")
        sys.exit(1)
    else:
        print(f"\n✅ All {len(results)} directories verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()