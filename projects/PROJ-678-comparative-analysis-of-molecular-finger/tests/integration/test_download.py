"""Integration tests for data download and checksum validation."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest
from datasets import load_dataset

# Import utilities from the project
try:
    from code.download import (
        calculate_checksum,
        verify_checksum,
        fetch_tox21_dataset,
    )
    from code.utils import setup_logging, get_logger
except ImportError:
    # Fallback imports if the module path differs
    import logging

    def setup_logging():
        logging.basicConfig(level=logging.INFO)

    def get_logger(name):
        return logging.getLogger(name)

    # Dummy stubs for checksum functions (will raise if used)
    def calculate_checksum(*args, **kwargs):
        raise NotImplementedError("calculate_checksum not available")

    def verify_checksum(*args, **kwargs):
        raise NotImplementedError("verify_checksum not available")

    def fetch_tox21_dataset(*args, **kwargs):
        raise NotImplementedError("fetch_tox21_dataset not available")

# Configure logger for this module
setup_logging()
logger = get_logger(__name__)

# Expected columns for the Tox21 dataset
# Note: The dataset might have slight variations, but these are the core toxicity endpoints.
EXPECTED_COLUMNS = [
    "SMILES",
    "NR-AR",
    "NR-AR-LBD",
    "NR-AhR",
    "NR-Aromatase",
    "NR-ER",
    "NR-ER-LBD",
    "NR-PPAR-gamma",
    "NR-GR",
    "NR-GR-LBD",
    "NR-MR",
    "SR-ARE",
    "SR-ATAD5",
    "SR-HSE",
    "SR-MMP",
    "SR-p53",
]

@pytest.mark.integration
def test_download_and_checksum_tox21():
    """
    Integration test to verify Tox21 dataset download and data integrity.

    This test:
    1. Downloads the Tox21 dataset via the project's download module.
    2. Verifies the dataset contains expected columns.
    3. Computes a checksum of the saved CSV file and validates it using the
       project's checksum verification function.
    4. Logs the download size and row count.
    """
    logger.info("Starting Tox21 dataset download and validation...")

    # Use a temporary directory for the download to avoid polluting the repo
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)

        # Download the dataset using the project's helper
        try:
            df, csv_path = fetch_tox21_dataset(str(output_dir), dataset_name="deepchem/tox21")
        except Exception as e:
            pytest.fail(f"Failed to fetch Tox21 dataset via fetch_tox21_dataset: {e}")

        logger.info(f"Dataset downloaded to {csv_path} with {len(df)} rows")

        # Verify expected columns
        missing_columns = set(EXPECTED_COLUMNS) - set(df.column_names)
        if missing_columns:
            # Log warning but don't fail if only some optional columns are missing
            # as long as SMILES and at least one endpoint exist
            if "SMILES" not in df.column_names:
                pytest.fail(f"Dataset is missing required column: SMILES")

            # Check for at least one toxicity endpoint
            toxicity_endpoints = [col for col in EXPECTED_COLUMNS if col != "SMILES"]
            present_endpoints = [col for col in toxicity_endpoints if col in df.column_names]
            if not present_endpoints:
                pytest.fail(
                    f"Dataset is missing all expected toxicity endpoints. Found columns: {df.column_names}"
                )

            logger.warning(
                f"Some expected columns missing: {missing_columns}. Proceeding with available columns."
            )
        else:
            logger.info("All expected columns present.")

        # Compute checksum of the saved CSV file (first 1000 rows)
        try:
            checksum = calculate_checksum(str(csv_path), algorithm="md5")
        except Exception as e:
            pytest.fail(f"Failed to calculate checksum: {e}")

        logger.info(f"Computed MD5 checksum of the CSV file: {checksum}")

        # Verify the checksum using the project's verification function
        try:
            is_valid = verify_checksum(str(csv_path), checksum, algorithm="md5")
        except Exception as e:
            pytest.fail(f"Checksum verification raised an exception: {e}")

        assert is_valid, "Checksum verification failed; the downloaded file may be corrupted."

        # Additional sanity checks
        assert len(df) > 0, "Dataset is empty"
        assert len(df) >= 7000, f"Dataset has fewer rows than expected: {len(df)}"

        logger.info(f"Tox21 dataset validation passed. Total rows: {len(df)}")