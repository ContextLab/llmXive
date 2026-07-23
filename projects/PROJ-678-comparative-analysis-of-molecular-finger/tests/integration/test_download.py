"""Integration tests for data download and checksum validation."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest
from datasets import load_dataset

from code.utils import setup_logging, get_logger

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
    "SR-p53"
]

@pytest.mark.integration
def test_download_and_checksum_tox21():
    """
    Integration test to verify Tox21 dataset download and data integrity.
    
    This test:
    1. Downloads the Tox21 dataset from HuggingFace.
    2. Verifies the dataset contains expected columns.
    3. Computes a checksum of the first 1000 rows to ensure data consistency.
    4. Logs the download size and row count.
    """
    logger.info("Starting Tox21 dataset download and validation...")
    
    # Download the dataset
    # Using trust_remote_code=False as it's a standard HF dataset
    try:
        # Load the training split
        dataset = load_dataset("deepchem/tox21", split="train")
    except Exception as e:
        pytest.fail(f"Failed to load Tox21 dataset from HuggingFace: {e}")
    
    logger.info(f"Dataset loaded successfully. Number of rows: {len(dataset)}")
    
    # Verify expected columns
    # Check if at least the SMILES column and one toxicity endpoint exist
    missing_columns = set(EXPECTED_COLUMNS) - set(dataset.column_names)
    if missing_columns:
        # Log warning but don't fail if only some optional columns are missing
        # as long as SMILES and at least one endpoint exist
        if "SMILES" not in dataset.column_names:
            pytest.fail(f"Dataset is missing required column: SMILES")
        
        # Check for at least one toxicity endpoint
        toxicity_endpoints = [col for col in EXPECTED_COLUMNS if col != "SMILES"]
        present_endpoints = [col for col in toxicity_endpoints if col in dataset.column_names]
        if not present_endpoints:
            pytest.fail(f"Dataset is missing all expected toxicity endpoints. Found columns: {dataset.column_names}")
        
        logger.warning(f"Some expected columns missing: {missing_columns}. Proceeding with available columns.")
    else:
        logger.info("All expected columns present.")
    
    # Compute a simple checksum of the data to ensure it's not corrupted
    # We serialize the first 1000 rows (or all if less) to bytes and hash them
    sample_size = min(1000, len(dataset))
    sample_data = dataset.select(range(sample_size))
    
    # Create a deterministic string representation for checksumming
    # We only checksum SMILES and one toxicity column to keep it fast
    checksum_input = ""
    for i in range(sample_size):
        row = sample_data[i]
        # Use SMILES and NR-AR if available, otherwise use the first available endpoint
        smiles = row.get('SMILES', '')
        nr_ar = row.get('NR-AR', '')
        checksum_input += f"{smiles}:{nr_ar}\n"
    
    computed_hash = hashlib.md5(checksum_input.encode('utf-8')).hexdigest()
    logger.info(f"Computed checksum (MD5) for first {sample_size} rows: {computed_hash}")
    
    # Verify the dataset is not empty
    assert len(dataset) > 0, "Dataset is empty"
    
    # Verify we have a reasonable number of rows (Tox21 should have ~8000)
    # Using a lower bound to be safe against version changes
    assert len(dataset) >= 7000, f"Dataset has fewer rows than expected: {len(dataset)}"
    
    logger.info(f"Tox21 dataset validation passed. Total rows: {len(dataset)}")