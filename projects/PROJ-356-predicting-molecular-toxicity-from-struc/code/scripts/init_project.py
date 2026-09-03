"""
Project Initialization Script for PROJ-356-predicting-molecular-toxicity-from-struc

This script programmatically creates the required directory structure for the
molecular toxicity prediction pipeline, ensuring reproducibility and proper
organization of code, data, models, and results.

Addresses:
- FR-001: Executability and Reproducibility
- Constitution Principle I: Scientific Rigor
- Constitution Principle V: Proper Project Structure
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional


# Base project root directory
PROJECT_ROOT = Path("projects/PROJ-356-predicting-molecular-toxicity-from-struc")


# Directory structure to create (relative to PROJECT_ROOT)
DIRECTORY_STRUCTURE = [
    "code",
    "code/src",
    "code/tests",
    "code/data",
    "code/data/raw",
    "code/data/processed",
    "code/results",
    "code/models",
    "code/config",
    "code/docs",
    "code/scripts",
    "code/state",
]


def create_directory_structure(base_path: Optional[Path] = None) -> Tuple[List[Path], List[Path]]:
    """
    Create the required directory structure for the project.

    Args:
        base_path: Base path for project root. Defaults to PROJECT_ROOT.

    Returns:
        Tuple of (created_paths, skipped_paths)
    """
    if base_path is None:
        base_path = PROJECT_ROOT

    created_paths: List[Path] = []
    skipped_paths: List[Path] = []

    # Ensure base path exists
    base_path.mkdir(parents=True, exist_ok=True)

    for dir_path in DIRECTORY_STRUCTURE:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
        except OSError as e:
            skipped_paths.append(full_path)
            print(f"Warning: Could not create {full_path}: {e}", file=sys.stderr)

    return created_paths, skipped_paths


def verify_structure(base_path: Optional[Path] = None) -> Tuple[bool, List[Path], List[Path]]:
    """
    Verify that all required directories exist.

    Args:
        base_path: Base path for project root. Defaults to PROJECT_ROOT.

    Returns:
        Tuple of (all_exist, existing_paths, missing_paths)
    """
    if base_path is None:
        base_path = PROJECT_ROOT

    existing_paths: List[Path] = []
    missing_paths: List[Path] = []

    for dir_path in DIRECTORY_STRUCTURE:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_paths.append(full_path)
        else:
            missing_paths.append(full_path)

    all_exist = len(missing_paths) == 0
    return all_exist, existing_paths, missing_paths


def main():
    """Main entry point for the initialization script."""
    parser = argparse.ArgumentParser(
        description="Initialize project directory structure for molecular toxicity prediction pipeline"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=PROJECT_ROOT,
        help=f"Base path for project root (default: {PROJECT_ROOT})"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing structure, do not create directories"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    print(f"Project Root: {args.base_path}")

    if args.verify_only:
        all_exist, existing, missing = verify_structure(args.base_path)
        if all_exist:
            print("✓ All required directories exist.")
            if args.verbose:
                for path in existing:
                    print(f"  - {path}")
        else:
            print("✗ Some directories are missing:")
            for path in missing:
                print(f"  - {path}")
            sys.exit(1)
    else:
        created, skipped = create_directory_structure(args.base_path)
        print(f"Created {len(created)} directories.")

        if args.verbose:
            for path in created:
                print(f"  ✓ {path}")

        if skipped:
            print(f"Skipped {len(skipped)} directories (already exist or permission error):")
            for path in skipped:
                print(f"  - {path}")

        # Verify final structure
        all_exist, existing, missing = verify_structure(args.base_path)
        if all_exist:
            print("✓ Verification passed: All required directories exist.")
        else:
            print("✗ Verification failed: Some directories could not be created.")
            for path in missing:
                print(f"  - {path}")
            sys.exit(1)


if __name__ == "__main__":
    main()