"""
Reproducibility Package Generator (Task T031)

Generates the final reproducibility package bundle for OSF publication.
Includes analysis results, anonymized logs, and documentation.
Explicitly excludes data/consent/ to satisfy Constitution Principle VI.
"""
import os
import sys
import tarfile
import json
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import List, Set

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Configuration
PACKAGE_VERSION = "v1.0"
OUTPUT_FILENAME = f"reproducibility_package_{PACKAGE_VERSION}.tar.gz"
OUTPUT_DIR = PROJECT_ROOT / "data"

# Inclusion list (relative to project root)
# Note: We include the essential scripts and data files required to rerun the analysis.
# We exclude large raw data (defects4j source) as per Plan.md scope, but include the
# stratified ground truth and summaries which are small enough.
INCLUDE_FILES = [
    "code/analysis/run_statistics.py",
    "code/analysis/bootstrap_utils.py",
    "code/analysis/correction_utils.py",
    "code/utils/config_manager.py",
    "code/utils/logging_utils.py",
    "code/utils/models.py",
    "code/utils/anonymize_logs.py",
    "code/download/download_defects4j.py",
    "code/simulation/participant_sim.py",
    "code/simulation/assignment_generator.py",
    "data/analysis_results/results.csv",
    "data/analysis_results/sensitivity_analysis.csv",
    "data/analysis_results/sensitivity_analysis_report.md",
    "data/analysis_results/outlier_flags.json",
    "data/interaction_logs/anonymized_logs.csv",
    "docs/README.md",
    "requirements.txt",
    "data/raw/defects4j/ground_truth.csv", # Small stratified sample
    "data/summaries/llm_summaries.csv",    # Pre-generated summaries
    "data/summaries/rule_summaries.csv",
]

# Exclusion list (patterns or specific paths)
EXCLUDE_PATTERNS = [
    "data/consent/",
    "data/raw/defects4j/source/", # Exclude large source code if present
    "data/summaries/cache/",
    "data/interaction_logs/raw_logs.csv",
    "data/analysis_results/baseline_results.json", # Intermediate artifact
    "state/",
    ".env",
    "__pycache__",
    "*.pyc",
    ".git",
    ".github",
    "data/reproducibility_package", # Avoid including previous packages
]

def should_exclude(file_path: str, exclude_patterns: List[str]) -> bool:
    """Check if a file path matches any exclusion pattern."""
    for pattern in exclude_patterns:
        if file_path.startswith(pattern) or file_path.endswith(pattern):
            return True
        # Check for directory traversal
        if pattern in file_path:
            return True
    return False

def verify_input_artifacts() -> bool:
    """Verify that all required input artifacts exist before packaging."""
    missing = []
    for file_path in INCLUDE_FILES:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            missing.append(file_path)
    
    if missing:
        logger.error(f"Missing required artifacts for reproducibility package: {missing}")
        return False
    
    logger.info("All required input artifacts verified.")
    return True

def create_reproducibility_package():
    """Create the tar.gz reproducibility package."""
    if not verify_input_artifacts():
        raise FileNotFoundError("Missing required input artifacts. Aborting package creation.")

    output_path = OUTPUT_DIR / OUTPUT_FILENAME
    logger.info(f"Creating reproducibility package at: {output_path}")

    # Use a temporary directory to stage files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        staging_dir = temp_path / "reproducibility_package"
        staging_dir.mkdir()

        # Copy files to staging directory, preserving structure
        for file_path in INCLUDE_FILES:
            src = PROJECT_ROOT / file_path
            if src.is_file():
                # Determine relative path for the archive
                # We want to flatten the structure slightly or keep it relative to root?
                # Let's keep relative to root but remove 'code/' prefix if it's too deep?
                # Standard practice: keep relative paths.
                dest = staging_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                logger.debug(f"Copied: {file_path}")
            else:
                logger.warning(f"Skipped non-existent file: {file_path}")

        # Create the tarball
        with tarfile.open(output_path, "w:gz") as tar:
            for root, dirs, files in os.walk(staging_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(staging_dir)
                    
                    # Double check exclusions (safety)
                    if should_exclude(str(arcname), EXCLUDE_PATTERNS):
                        logger.debug(f"Excluding from archive: {arcname}")
                        continue
                        
                    tar.add(file_path, arcname=arcname)
        
        # Verify the package
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Package created successfully: {output_path.name} ({size_mb:.2f} MB)")
            
            # Generate checksum
            with open(output_path, "rb") as f:
                sha256_hash = hashlib.sha256(f.read()).hexdigest()
            logger.info(f"SHA-256: {sha256_hash}")
            
            # Save checksum file
            checksum_file = OUTPUT_DIR / f"{OUTPUT_FILENAME}.sha256"
            with open(checksum_file, "w") as f:
                f.write(f"{sha256_hash}  {OUTPUT_FILENAME}\n")
            logger.info(f"Checksum saved to: {checksum_file}")
            
            return output_path
        else:
            raise RuntimeError("Failed to create package file.")

def main():
    """Entry point for the script."""
    logger.info("Starting Reproducibility Package Generation (T031)")
    try:
        package_path = create_reproducibility_package()
        logger.info(f"SUCCESS: Reproducibility package generated at {package_path}")
        return 0
    except Exception as e:
        logger.error(f"FAILED: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
