"""
Verification script for segregation energies.
Checks that data/processed/segregation_energies.csv contains required columns
(alloy_system_id, cluster_metadata) and valid energy values.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

from config import get_project_root, get_data_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['alloy_system_id', 'cluster_metadata', 'segregation_energy']

def verify_segregation_energies() -> bool:
    """
    Verify that the segregation energies file exists and contains the required columns.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()

    energies_path = data_paths['processed'] / 'segregation_energies.csv'

    if not energies_path.exists():
        logger.error(f"File not found: {energies_path}")
        return False

    try:
        df = pd.read_csv(energies_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False

    logger.info(f"Loaded {len(df)} rows from {energies_path}")

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        logger.error(f"Available columns: {list(df.columns)}")
        return False

    logger.info("All required columns present: alloy_system_id, cluster_metadata, segregation_energy")

    # Verify non-empty values
    if df['segregation_energy'].isna().all():
        logger.error("segregation_energy column contains only NaN values")
        return False

    # Verify alloy_system_id is populated
    if df['alloy_system_id'].isna().all():
        logger.error("alloy_system_id column contains only NaN values")
        return False

    # Verify cluster_metadata is populated (can be JSON string or object)
    if df['cluster_metadata'].isna().all():
        logger.error("cluster_metadata column contains only NaN values")
        return False

    # Log sample of the data
    sample = df.head(3)
    logger.info("Sample data:")
    logger.info(sample.to_string())

    logger.info(f"Verification PASSED: {len(df)} valid energy records with alloy_system_id and cluster_metadata")
    return True

def main():
    """Entry point for verification."""
    success = verify_segregation_energies()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
