"""
Integration test for T012b: Artifact verification test.

Logic: Verify that the following artifacts exist and contain non-empty data:
1. data/processed/gb_supercells/ (directory with files)
2. data/processed/descriptors.csv (CSV with data rows)
3. data/processed/segregation_energies.csv (CSV with data rows)

This test assumes the pipeline (T013, T014, T015, T017c) has been executed
and produced the required outputs. If these files do not exist or are empty,
the test fails.
"""
import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_project_root, get_data_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArtifactVerificationError(Exception):
    """Custom exception for artifact verification failures."""
    pass

def verify_gb_supercells_directory() -> bool:
    """
    Verify that data/processed/gb_supercells/ exists and contains files.
    
    Returns:
        True if directory exists and has files, False otherwise.
        
    Raises:
        ArtifactVerificationError: If directory is missing or empty.
    """
    data_paths = get_data_paths()
    gb_supercells_dir = data_paths['processed'] / 'gb_supercells'
    
    logger.info(f"Checking GB supercells directory: {gb_supercells_dir}")
    
    if not gb_supercells_dir.exists():
        error_msg = f"GB supercells directory does not exist: {gb_supercells_dir}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)
    
    files = list(gb_supercells_dir.glob("*"))
    if not files:
        error_msg = f"GB supercells directory is empty: {gb_supercells_dir}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)
    
    logger.info(f"Found {len(files)} files in GB supercells directory")
    return True

def verify_descriptors_csv() -> bool:
    """
    Verify that data/processed/descriptors.csv exists and contains data.
    
    Returns:
        True if file exists and has data rows, False otherwise.
        
    Raises:
        ArtifactVerificationError: If file is missing or empty.
    """
    data_paths = get_data_paths()
    descriptors_file = data_paths['processed'] / 'descriptors.csv'
    
    logger.info(f"Checking descriptors file: {descriptors_file}")
    
    if not descriptors_file.exists():
        error_msg = f"Descriptors file does not exist: {descriptors_file}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)
    
    try:
        df = pd.read_csv(descriptors_file)
        if df.empty:
            error_msg = f"Descriptors file exists but contains no data rows: {descriptors_file}"
            logger.error(error_msg)
            raise ArtifactVerificationError(error_msg)
        
        logger.info(f"Descriptors file contains {len(df)} rows with columns: {list(df.columns)}")
        return True
    except Exception as e:
        error_msg = f"Failed to read descriptors file: {e}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)

def verify_segregation_energies_csv() -> bool:
    """
    Verify that data/processed/segregation_energies.csv exists and contains data.
    
    Returns:
        True if file exists and has data rows, False otherwise.
        
    Raises:
        ArtifactVerificationError: If file is missing or empty.
    """
    data_paths = get_data_paths()
    energies_file = data_paths['processed'] / 'segregation_energies.csv'
    
    logger.info(f"Checking segregation energies file: {energies_file}")
    
    if not energies_file.exists():
        error_msg = f"Segregation energies file does not exist: {energies_file}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)
    
    try:
        df = pd.read_csv(energies_file)
        if df.empty:
            error_msg = f"Segregation energies file exists but contains no data rows: {energies_file}"
            logger.error(error_msg)
            raise ArtifactVerificationError(error_msg)
        
        logger.info(f"Segregation energies file contains {len(df)} rows with columns: {list(df.columns)}")
        
        # Verify required columns exist
        required_columns = ['energy', 'alloy_system_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"Segregation energies file missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise ArtifactVerificationError(error_msg)
        
        return True
    except Exception as e:
        error_msg = f"Failed to read segregation energies file: {e}"
        logger.error(error_msg)
        raise ArtifactVerificationError(error_msg)

def test_all_artifacts_exist():
    """
    Main test function that verifies all required artifacts.
    
    This test will fail loudly if any artifact is missing or empty.
    """
    verification_results = []
    
    try:
        # Verify GB supercells directory
        gb_result = verify_gb_supercells_directory()
        verification_results.append(("gb_supercells_directory", gb_result))
    except ArtifactVerificationError as e:
        verification_results.append(("gb_supercells_directory", False))
        logger.error(f"GB supercells verification failed: {e}")
    
    try:
        # Verify descriptors CSV
        desc_result = verify_descriptors_csv()
        verification_results.append(("descriptors_csv", desc_result))
    except ArtifactVerificationError as e:
        verification_results.append(("descriptors_csv", False))
        logger.error(f"Descriptors verification failed: {e}")
    
    try:
        # Verify segregation energies CSV
        energy_result = verify_segregation_energies_csv()
        verification_results.append(("segregation_energies_csv", energy_result))
    except ArtifactVerificationError as e:
        verification_results.append(("segregation_energies_csv", False))
        logger.error(f"Segregation energies verification failed: {e}")
    
    # Summary
    logger.info("=" * 50)
    logger.info("ARTIFACT VERIFICATION SUMMARY")
    logger.info("=" * 50)
    
    all_passed = True
    for artifact_name, passed in verification_results:
        status = "PASS" if passed else "FAIL"
        logger.info(f"{artifact_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 50)
    
    if not all_passed:
        failed_artifacts = [name for name, passed in verification_results if not passed]
        pytest.fail(f"Artifact verification failed for: {', '.join(failed_artifacts)}")
    
    logger.info("All artifact verifications passed!")

if __name__ == "__main__":
    test_all_artifacts_exist()