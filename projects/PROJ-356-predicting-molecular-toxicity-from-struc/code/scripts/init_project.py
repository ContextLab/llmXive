"""
Project Initialization Script for llmXive Automated Science Pipeline.

This script programmatically creates the required directory structure
for the molecular toxicity prediction project.

Usage:
    python code/scripts/init_project.py [--project-root <path>]

If --project-root is not provided, it defaults to the parent directory
of the script's location (i.e., the project root).
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
    "code",
    "code/src",
    "code/src/features",
    "code/src/models",
    "code/src/pipeline",
    "code/src/utils",
    "code/src/data",
    "code/src/evaluation",
    "code/tests",
    "code/tests/unit",
    "code/tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "data/external",
    "results",
    "results/plots",
    "results/reports",
    "models",
    "config",
    "docs",
    "contracts",
    "scripts",
    "specs",
]

def create_directory_structure(root: Path, dirs: List[str]) -> List[Tuple[Path, bool]]:
    """
    Create directory structure and return a list of (path, created) tuples.
    
    Args:
        root: The project root path
        dirs: List of relative directory paths to create
        
    Returns:
        List of (absolute_path, was_created) tuples
    """
    results = []
    for dir_path in dirs:
        full_path = root / dir_path
        was_created = False
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            was_created = True
        results.append((full_path, was_created))
    return results

def verify_structure(root: Path, dirs: List[str]) -> Tuple[bool, List[Path]]:
    """
    Verify that all required directories exist.
    
    Args:
        root: The project root path
        dirs: List of relative directory paths to verify
        
    Returns:
        Tuple of (all_exist, list_of_missing_paths)
    """
    missing = []
    for dir_path in dirs:
        full_path = root / dir_path
        if not full_path.exists():
            missing.append(full_path)
        elif not full_path.is_dir():
            missing.append(full_path)
    return len(missing) == 0, missing

def main(project_root: Optional[Path] = None) -> int:
    """
    Main entry point for project initialization.
    
    Args:
        project_root: Optional explicit project root path. If None,
                    defaults to the parent of this script's directory.
                    
    Returns:
        Exit code: 0 for success, 1 for failure
    """
    if project_root is None:
        # Default to parent of script directory
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
        
        # Verify we're in the expected location
        if not (project_root / "tasks.md").exists():
            # Try to find tasks.md by walking up
            current = project_root
            while current != current.parent:
                if (current / "tasks.md").exists():
                    project_root = current
                    break
                current = current.parent
    
    print(f"Project root: {project_root}")
    
    # Create directory structure
    print("Creating directory structure...")
    results = create_directory_structure(project_root, REQUIRED_DIRS)
    
    created_count = sum(1 for _, created in results if created)
    total_count = len(results)
    
    print(f"Created {created_count} new directories.")
    print(f"Total directories: {total_count}")
    
    # Verify structure
    all_exist, missing = verify_structure(project_root, REQUIRED_DIRS)
    
    if not all_exist:
        print("ERROR: The following directories are missing after creation:")
        for path in missing:
            print(f"  - {path}")
        return 1
    
    print("\nDirectory structure verification: PASSED")
    
    # Print summary
    print("\nCreated structure:")
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        print(f"  [OK] {full_path}")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize project directory structure for llmXive pipeline"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Explicit project root path (default: parent of script directory)"
    )
    
    args = parser.parse_args()
    exit_code = main(args.project_root)
    sys.exit(exit_code)
