"""
Verify no PEMS-SF files exist in data/raw/ directory.

Dataset Requirements:
- Only 3 UCI datasets allowed: Electricity, Traffic, Synthetic Control Chart
- PEMS-SF files must NOT exist in data/raw/

This script checks the data directory and reports findings.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define project root and data directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Required datasets (3 UCI datasets only)
REQUIRED_DATASETS = {
    "Electricity": ["electricity.csv", "Electricity.csv"],
    "Traffic": ["traffic.csv", "Traffic.csv"],
    "Synthetic Control Chart": ["synthetic_control_chart.csv", "synthetic_control.csv"]
}

# PEMS-SF patterns to check for
PEMS_SF_PATTERNS = [
    "pems",
    "PEMS",
    "pems_sf",
    "PEMS-SF",
    "pems-sf",
    "PEMS_SF"
]

def check_for_pems_sf_files(data_dir: Path) -> list:
    """
    Check for any PEMS-SF related files in the data directory.
    
    Args:
        data_dir: Path to data/raw/ directory
        
    Returns:
        List of PEMS-SF files found (empty if none)
    """
    pems_files = []
    
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return pems_files
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            filename = file_path.name.lower()
            for pattern in PEMS_SF_PATTERNS:
                if pattern.lower() in filename:
                    pems_files.append(str(file_path.relative_to(PROJECT_ROOT)))
                    break
    
    return pems_files

def check_required_datasets(data_dir: Path) -> dict:
    """
    Check if required UCI datasets exist in data/raw/.
    
    Args:
        data_dir: Path to data/raw/ directory
        
    Returns:
        Dictionary with dataset names and their status
    """
    dataset_status = {}
    
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        for dataset_name in REQUIRED_DATASETS:
            dataset_status[dataset_name] = {
                "found": False,
                "files": [],
                "message": "Data directory does not exist"
            }
        return dataset_status
    
    for dataset_name, filenames in REQUIRED_DATASETS.items():
        found_files = []
        for filename in filenames:
            file_path = data_dir / filename
            if file_path.exists():
                found_files.append(str(file_path.relative_to(PROJECT_ROOT)))
        
        if found_files:
            dataset_status[dataset_name] = {
                "found": True,
                "files": found_files,
                "message": f"Found {len(found_files)} file(s)"
            }
        else:
            dataset_status[dataset_name] = {
                "found": False,
                "files": [],
                "message": "Dataset not found"
            }
    
    return dataset_status

def list_all_files_in_data_raw(data_dir: Path) -> list:
    """
    List all files in data/raw/ directory for reference.
    
    Args:
        data_dir: Path to data/raw/ directory
        
    Returns:
        List of all file paths in data/raw/
    """
    all_files = []
    
    if not data_dir.exists():
        return all_files
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            all_files.append(str(file_path.relative_to(PROJECT_ROOT)))
    
    return all_files

def main():
    """
    Main verification function.
    
    Checks:
    1. No PEMS-SF files exist in data/raw/
    2. Required UCI datasets exist (Electricity, Traffic, Synthetic Control Chart)
    3. Reports all files in data/raw/ for reference
    """
    logger.info("=" * 60)
    logger.info("PEMS-SF File Verification")
    logger.info("=" * 60)
    
    # Check 1: Verify no PEMS-SF files exist
    logger.info("\n[CHECK 1] Verifying no PEMS-SF files exist...")
    pems_files = check_for_pems_sf_files(DATA_RAW_DIR)
    
    if pems_files:
        logger.error(f"FAILED: Found {len(pems_files)} PEMS-SF file(s):")
        for pems_file in pems_files:
            logger.error(f"  - {pems_file}")
        check1_passed = False
    else:
        logger.info("PASSED: No PEMS-SF files found in data/raw/")
        check1_passed = True
    
    # Check 2: Verify required datasets exist
    logger.info("\n[CHECK 2] Verifying required UCI datasets exist...")
    dataset_status = check_required_datasets(DATA_RAW_DIR)
    
    required_passed = True
    for dataset_name, status in dataset_status.items():
        if status["found"]:
            logger.info(f"PASSED: {dataset_name} - {status['message']}")
        else:
            logger.warning(f"WARNING: {dataset_name} - {status['message']}")
            required_passed = False
    
    # Check 3: List all files for reference
    logger.info("\n[CHECK 3] Listing all files in data/raw/...")
    all_files = list_all_files_in_data_raw(DATA_RAW_DIR)
    
    if all_files:
        logger.info(f"Found {len(all_files)} file(s) in data/raw/:")
        for file_path in all_files:
            file_size = (DATA_RAW_DIR / file_path).stat().st_size
            logger.info(f"  - {file_path} ({file_size:,} bytes)")
    else:
        logger.info("No files found in data/raw/")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Check 1 (No PEMS-SF files): {'PASSED' if check1_passed else 'FAILED'}")
    logger.info(f"Check 2 (Required datasets): {'PASSED' if required_passed else 'WARNING'}")
    
    # Final verdict
    if check1_passed:
        logger.info("\nOVERALL: VERIFICATION PASSED")
        logger.info("No PEMS-SF files exist in data/raw/ directory.")
        sys.exit(0)
    else:
        logger.error("\nOVERALL: VERIFICATION FAILED")
        logger.error("PEMS-SF files found in data/raw/ directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
