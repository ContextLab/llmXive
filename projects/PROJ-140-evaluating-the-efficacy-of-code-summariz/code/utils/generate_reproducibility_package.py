import os
import sys
import tarfile
import json
from pathlib import Path
from typing import List, Optional

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_utils import get_logger, setup_logging

logger = get_logger(__name__)

# Configuration
PACKAGE_NAME = "reproducibility_package_v1.0"
OUTPUT_DIR = project_root / "data"
PACKAGE_PATH = OUTPUT_DIR / f"{PACKAGE_NAME}.tar.gz"

# Files to include in the package
SCRIPTS_TO_INCLUDE = [
    "code/analysis/run_statistics.py",
    "code/analysis/bootstrap_utils.py",
    "code/analysis/correction_utils.py",
    "code/utils/config_manager.py",
    "code/utils/hash_artifacts.py",
    "code/utils/logging_utils.py",
    "code/utils/models.py",
    "code/setup_project_structure.py",
    "code/data_prep/download_defects4j.py",
    "code/data_prep/generate_summaries.py",
]

DATA_FILES_TO_INCLUDE = [
    "data/analysis_results/results.csv",
    "data/interaction_logs/anonymized_logs.csv",
    "README.md",
]

# Directories to include (excluding consent)
DIRECTORIES_TO_INCLUDE = [
    "code/analysis",
    "code/utils",
    "code/data_prep",
]

# Explicitly excluded paths (Constitution Principle VI)
EXCLUDED_PATHS = [
    "data/consent",
    "data/consent/",
    "data/consent/*",
]

def should_exclude(tarinfo: str) -> bool:
    """Check if a path should be excluded from the package."""
    path_lower = tarinfo.lower()
    for excluded in EXCLUDED_PATHS:
        if excluded.lower() in path_lower:
            return True
    return False

def create_reproducibility_package(
    scripts: List[str],
    data_files: List[str],
    directories: List[str],
    output_path: Path,
) -> bool:
    """
    Create a tar.gz reproducibility package containing scripts, data, and README.
    
    Args:
        scripts: List of script file paths to include
        data_files: List of data file paths to include
        directories: List of directories to include
        output_path: Path where the tar.gz file will be saved
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Creating reproducibility package at: {output_path}")
    
    if not output_path.parent.exists():
        logger.error(f"Output directory does not exist: {output_path.parent}")
        return False
    
    try:
        with tarfile.open(output_path, "w:gz") as tar:
            # Add individual scripts
            for script in scripts:
                script_path = project_root / script
                if script_path.exists():
                    tar.add(script_path, arcname=script)
                    logger.debug(f"Added script: {script}")
                else:
                    logger.warning(f"Script not found, skipping: {script}")
            
            # Add data files
            for data_file in data_files:
                data_path = project_root / data_file
                if data_path.exists():
                    tar.add(data_path, arcname=data_file)
                    logger.debug(f"Added data file: {data_file}")
                else:
                    logger.warning(f"Data file not found, skipping: {data_file}")
            
            # Add directories (recursively)
            for directory in directories:
                dir_path = project_root / directory
                if dir_path.exists() and dir_path.is_dir():
                    for root, dirs, files in os.walk(dir_path):
                        # Filter out excluded directories
                        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
                        
                        for file in files:
                            file_path = Path(root) / file
                            if not should_exclude(str(file_path)):
                                arcname = str(file_path.relative_to(project_root))
                                tar.add(file_path, arcname=arcname)
                                logger.debug(f"Added directory file: {arcname}")
                else:
                    logger.warning(f"Directory not found, skipping: {directory}")
            
            # Verify package contents
            tar.close()
            
            # Re-open to verify
            with tarfile.open(output_path, "r:gz") as tar_verify:
                members = tar_verify.getnames()
                logger.info(f"Package created with {len(members)} members")
                
                # Log first few members for verification
                for member in members[:10]:
                    logger.debug(f"  - {member}")
                if len(members) > 10:
                    logger.debug(f"  ... and {len(members) - 10} more")
            
            # Verify consent directory is NOT included
            for member in members:
                if "consent" in member.lower():
                    logger.error(f"SECURITY VIOLATION: Consent data found in package: {member}")
                    return False
            
            logger.info("Reproducibility package created successfully")
            return True
            
    except Exception as e:
        logger.error(f"Failed to create reproducibility package: {e}")
        return False

def main():
    """Main entry point for generating the reproducibility package."""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("Starting Reproducibility Package Generation (T031)")
    logger.info("=" * 60)
    
    # Verify required files exist before creating package
    missing_files = []
    for file_path in DATA_FILES_TO_INCLUDE:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error("Required data files are missing. Cannot create package.")
        for f in missing_files:
            logger.error(f"  Missing: {f}")
        logger.error("Please ensure T024 (Analysis) and T015/T016 (Interaction Logs) are complete.")
        return 1
    
    # Create the package
    success = create_reproducibility_package(
        scripts=SCRIPTS_TO_INCLUDE,
        data_files=DATA_FILES_TO_INCLUDE,
        directories=DIRECTORIES_TO_INCLUDE,
        output_path=PACKAGE_PATH,
    )
    
    if success:
        logger.info(f"Package successfully created: {PACKAGE_PATH}")
        logger.info("Package contents verified. No consent data included.")
        logger.info("Ready for OSF publication (FR-007).")
        return 0
    else:
        logger.error("Failed to create reproducibility package.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
