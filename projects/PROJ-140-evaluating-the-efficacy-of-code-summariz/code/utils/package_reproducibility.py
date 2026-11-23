"""
Reproducibility Package Generator (Task T031)

Generates a tar.gz archive containing all necessary scripts, data artifacts,
and documentation to reproduce the study results on a fresh environment.

Excludes sensitive data (consent forms, raw logs) and large source datasets
(Defects4J) as per the project's data management plan.
"""

import os
import sys
import tarfile
import json
import shutil
import tempfile
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities for logging and configuration
# Using relative imports to match the project structure
try:
    from utils.logging_utils import get_logger, setup_logging
    from utils.config_manager import get_config
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    def setup_logging():
        pass
    def get_config():
        return {}

logger = get_logger(__name__)

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_DIR = PROJECT_ROOT / "state"
REPRODUCIBILITY_OUTPUT = DATA_DIR / "reproducibility_package_v1.0.tar.gz"

# Configuration for inclusion/exclusion
EXCLUDED_DIRS = [
    "data/consent",
    "data/raw/defects4j",
    "data/interaction_logs/raw_logs.csv",
    "__pycache__",
    ".git",
    ".github",
    "venv",
    ".env",
    "data/interaction_logs/missing_ground_truth.json" # Sensitive internal flag
]

REQUIRED_ARTIFACTS = [
    # Core Scripts
    "code/main.py",
    "code/utils/package_reproducibility.py",
    "code/utils/hash_artifacts.py",
    "code/utils/logging_utils.py",
    "code/utils/config_manager.py",
    "code/utils/anonymize_logs.py",
    "code/download/download_defects4j.py",
    "code/analysis/run_statistics.py",
    "code/analysis/bootstrap_utils.py",
    "code/analysis/correction_utils.py",
    "code/analysis/generate_report.py",
    "code/analysis/load_data.py",
    "code/simulation/latency_calibrator.py",
    "code/simulation/assignment_generator.py",
    # Dependencies
    "requirements.txt",
    # Documentation
    "docs/README.md",
    # State & Results
    "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/artifact_hashes.yaml",
    "data/analysis_results/results.csv",
    "data/interaction_logs/anonymized_logs.csv",
    "data/summaries/llm_summaries_sim.csv",
    "data/summaries/rule_summaries.csv"
]

def should_exclude(path: Path, project_root: Path) -> bool:
    """
    Determine if a file or directory should be excluded from the archive.
    """
    rel_path = path.relative_to(project_root).as_posix()

    # Check against explicit exclusion list
    for excluded in EXCLUDED_DIRS:
        if rel_path.startswith(excluded):
            logger.debug(f"Excluding path: {rel_path} (matches {excluded})")
            return True

    # Check if it's a hidden file or directory (except .github which is needed for CI)
    if path.name.startswith('.') and path.name != '.github':
        logger.debug(f"Excluding hidden path: {rel_path}")
        return True

    return False

def verify_input_artifacts(required_files: List[str], project_root: Path) -> bool:
    """
    Verify that all required artifacts exist before packaging.
    Returns True if all exist, False otherwise.
    """
    missing = []
    for rel_path in required_files:
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)

    if missing:
        logger.error(f"Missing required artifacts: {missing}")
        logger.error("Cannot generate reproducibility package without these files.")
        return False

    logger.info(f"Verified {len(required_files)} required artifacts.")
    return True

def create_reproducibility_package(
    output_path: Path,
    project_root: Path,
    required_files: Optional[List[str]] = None
) -> bool:
    """
    Creates the tar.gz reproducibility package.

    Args:
        output_path: Path where the .tar.gz will be saved.
        project_root: Root directory of the project.
        required_files: List of relative paths that MUST be included.

    Returns:
        True if successful, False otherwise.
    """
    if required_files is None:
        required_files = REQUIRED_ARTIFACTS

    # 1. Verify inputs
    if not verify_input_artifacts(required_files, project_root):
        return False

    # 2. Create a temporary directory to stage the files
    # This ensures we don't accidentally include unwanted files from the root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_staging = Path(temp_dir) / "reproducibility_package"
        temp_staging.mkdir()

        logger.info(f"Staging files in {temp_staging}...")

        # 3. Copy required files explicitly
        for rel_path in required_files:
            src = project_root / rel_path
            if not src.exists():
                # Should have been caught by verify_input_artifacts, but double check
                logger.warning(f"Skipping missing file during copy: {rel_path}")
                continue

            dst = temp_staging / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            logger.debug(f"Copied: {rel_path}")

        # 4. Add dynamic metadata file (optional but good practice)
        metadata = {
            "package_version": "1.0",
            "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
            "generated_at": str(Path(__file__).parent.parent.parent.stat().st_mtime), # Approx
            "excluded_patterns": EXCLUDED_DIRS
        }
        metadata_path = temp_staging / "package_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # 5. Create the tar.gz archive
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Creating archive: {output_path}")

        with tarfile.open(output_path, "w:gz") as tar:
            # Add the staging directory contents to the root of the archive
            for item in temp_staging.iterdir():
                tar.add(item, arcname=item.name)

        # 6. Verify the archive size and existence
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Successfully created {output_path.name} ({size_mb:.2f} MB)")
            return True
        else:
            logger.error("Failed to create archive file.")
            return False

def main():
    """
    Entry point for the reproducibility package generator.
    """
    setup_logging()
    logger.info("Starting Reproducibility Package Generation (T031)...")

    try:
        success = create_reproducibility_package(
            output_path=REPRODUCIBILITY_OUTPUT,
            project_root=PROJECT_ROOT,
            required_files=REQUIRED_ARTIFACTS
        )

        if success:
            logger.info("Reproducibility package generated successfully.")
            sys.exit(0)
        else:
            logger.error("Failed to generate reproducibility package.")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error during packaging: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()