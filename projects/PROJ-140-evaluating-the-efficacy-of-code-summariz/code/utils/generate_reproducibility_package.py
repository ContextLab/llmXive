"""
Reproducibility Package Generator for PROJ-140.

This script generates a final reproducibility package bundle (tar.gz) containing:
- All analysis scripts (code/analysis/)
- Data preparation scripts (code/data_prep/)
- Utility scripts (code/utils/)
- Anonymized interaction logs (data/interaction_logs/anonymized_logs.csv)
- Analysis results (data/analysis_results/results.csv)
- README.md
- Configuration files (.env.example, requirements.txt)

Explicitly EXCLUDES:
- data/consent/ (Constitution Principle VI - Sensitive Data)
- data/defects4j/raw/ (Large raw downloads, not needed for re-analysis)
- data/summaries/llm_sim_summaries.csv (Generated artifact, not source)
- data/interaction_logs/raw_logs.csv (Sensitive raw logs)
- state/ (Internal state)
- .git/ (Version control data)
- __pycache__/ (Python cache)
- *.pyc (Compiled Python)

Output: data/reproducibility_package_v1.0.tar.gz
"""

import os
import sys
import tarfile
import json
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from utils.logging_utils import get_logger, setup_logging
from utils.config_manager import get_config

# Initialize logger
setup_logging()
logger = get_logger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directories to include
INCLUDE_DIRS = [
    "code/analysis",
    "code/data_prep",
    "code/utils",
    "code/tests",  # Include tests for verification
    "data/analysis_results",
    "data/interaction_logs",
    "contracts",
    "specs",
]

# Specific files to include (relative to project root)
INCLUDE_FILES = [
    "README.md",
    "requirements.txt",
    ".env.example",
    "tasks.md",
    "data-model.md",
    "spec.md",
    "plan.md",
]

# Patterns to exclude (glob patterns)
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git",
    ".gitignore",
    ".env",  # Real secrets, not example
    "data/consent",  # Sensitive data - Constitution Principle VI
    "data/defects4j/raw",  # Large raw downloads
    "data/interaction_logs/raw_logs.csv",  # Sensitive raw logs
    "data/summaries/llm_sim_summaries.csv",  # Generated artifact
    "data/summaries/rule_summaries.csv",  # Generated artifact
    "state",  # Internal state
    "data/analysis_results/outlier_flags.json",  # Intermediate artifact
    "data/analysis_results/sensitivity_analysis.csv",  # Intermediate artifact
    "data/analysis_results/baseline_results.json",  # Intermediate artifact
]

# Output file path
OUTPUT_FILENAME = "reproducibility_package_v1.0.tar.gz"
OUTPUT_PATH = PROJECT_ROOT / "data" / OUTPUT_FILENAME


def should_exclude(tarinfo: tarfile.TarInfo, base_path: Path) -> bool:
    """
    Determine if a file/directory should be excluded from the package.

    Args:
        tarinfo: TarInfo object from tarfile
        base_path: Base path of the file relative to project root

    Returns:
        True if the file should be excluded, False otherwise
    """
    name = tarinfo.name

    # Check against exclusion patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern in name or name.endswith(pattern):
            logger.debug(f"Excluding: {name} (matches pattern: {pattern})")
            return True

    # Check if it's a hidden file (starts with .) except .env.example
    if name.startswith(".") and name != ".env.example":
        logger.debug(f"Excluding hidden file: {name}")
        return True

    return False


def create_reproducibility_package(output_path: Path, project_root: Path) -> str:
    """
    Create the reproducibility package bundle.

    Args:
        output_path: Path where the tar.gz file will be created
        project_root: Root directory of the project

    Returns:
        Path to the created package
    """
    logger.info(f"Creating reproducibility package at: {output_path}")

    # Verify input data exists
    required_files = [
        project_root / "data" / "analysis_results" / "results.csv",
        project_root / "data" / "interaction_logs" / "anonymized_logs.csv",
        project_root / "README.md",
    ]

    for req_file in required_files:
        if not req_file.exists():
            logger.error(f"Required file missing: {req_file}")
            raise FileNotFoundError(f"Required file missing: {req_file}")

    # Create the tar.gz archive
    with tarfile.open(output_path, "w:gz") as tar:
        # Add directories
        for dir_path in INCLUDE_DIRS:
            full_path = project_root / dir_path
            if full_path.exists():
                logger.info(f"Adding directory: {dir_path}")
                # Add with recursive=True to include all subdirectories
                tar.add(
                    full_path,
                    arcname=dir_path,
                    filter=lambda member: member if not should_exclude(member, full_path) else None,
                )

        # Add specific files
        for file_path in INCLUDE_FILES:
            full_path = project_root / file_path
            if full_path.exists():
                logger.info(f"Adding file: {file_path}")
                tar.add(
                    full_path,
                    arcname=file_path,
                    filter=lambda member: member if not should_exclude(member, full_path) else None,
                )
            else:
                logger.warning(f"File not found, skipping: {file_path}")

    # Verify the created package
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Package created successfully: {output_path} ({size_mb:.2f} MB)")

        # List contents for verification
        logger.info("Package contents:")
        with tarfile.open(output_path, "r:gz") as tar:
            for member in tar.getmembers():
                logger.debug(f"  - {member.name} ({member.size} bytes)")
    else:
        logger.error("Package creation failed - file not found")
        raise RuntimeError("Package creation failed")

    return str(output_path)


def main():
    """Main entry point for the reproducibility package generator."""
    try:
        # Create output directory if it doesn't exist
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing package if it exists
        if OUTPUT_PATH.exists():
            logger.info(f"Removing existing package: {OUTPUT_PATH}")
            OUTPUT_PATH.unlink()

        # Create the package
        package_path = create_reproducibility_package(OUTPUT_PATH, PROJECT_ROOT)

        logger.info(f"Reproducibility package generated successfully: {package_path}")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate reproducibility package: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
