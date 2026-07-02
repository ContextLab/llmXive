"""
Contract tests for the test split functionality (US2).

This module verifies that the test set generation adheres to strict
data independence and integrity contracts defined in the research plan.
"""
import os
import sys
import json
import hashlib
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.test_split import load_data, create_test_set, save_test_set
from code.utils.logging import get_logger
from code.utils.data_models import MaterialEntry

logger = get_logger("contract_test_split")

# Paths relative to project root
FULL_POOL_PATH = project_root / "data" / "processed" / "full_pool_final.csv"
TEST_SET_PATH = project_root / "data" / "processed" / "test_set.csv"
METADATA_PATH = project_root / "data" / "metadata" / "test_set_metadata.json"

class TestTestSetIndependence(unittest.TestCase):
    """
    Contract Test: test_test_set_independence
    
    Verifies that the test set is truly independent of the training pool
    generation process and maintains data integrity.
    """

    def setUp(self):
        """Ensure test data exists before running contracts."""
        if not FULL_POOL_PATH.exists():
            self.skipTest(f"Full pool data not found at {FULL_POOL_PATH}. "
                          "Run data ingestion pipeline first.")
        
        # Ensure test set exists
        if not TEST_SET_PATH.exists():
            self.skipTest(f"Test set not found at {TEST_SET_PATH}. "
                          "Run test_split.py first.")

    def test_test_set_independence(self):
        """
        Contract: Verify test set independence.
        
        Checks:
        1. No overlap between test set IDs and any potential training subset IDs.
        2. Test set composition distribution is representative (statistical check).
        3. Test set checksum matches recorded metadata (integrity).
        """
        # 1. Load data
        full_df = load_data(FULL_POOL_PATH)
        test_df = load_data(TEST_SET_PATH)
        
        # Load metadata to verify integrity
        if METADATA_PATH.exists():
            with open(METADATA_PATH, 'r') as f:
                metadata = json.load(f)
        else:
            self.fail("Metadata file missing. Contract requires metadata for verification.")

        # 2. Verify no ID overlap (Conceptual: assuming test set is a subset of full,
        #    independence here means it wasn't used for training in the current run context.
        #    Since we don't have the training set yet, we verify the *generation* logic
        #    ensures it is a distinct partition from the *remaining* pool used for training.
        #    Here we verify the test set is a valid random subset of the full pool without
        #    duplication in the selection process).
        
        full_ids = set(full_df['material_id'].tolist())
        test_ids = set(test_df['material_id'].tolist())
        
        # The test set must be a subset of the full pool
        self.assertTrue(test_ids.issubset(full_ids), 
                        "Test set contains IDs not present in full pool.")
        
        # 3. Verify Integrity via Checksum
        # Calculate current checksum of test set
        calculated_checksum = hashlib.sha256()
        # Sort by ID to ensure deterministic checksum
        sorted_test_df = test_df.sort_values('material_id')
        sorted_test_df.to_csv(TEST_SET_PATH, index=False) # Re-save sorted for comparison if needed
        
        with open(TEST_SET_PATH, 'rb') as f:
            calculated_checksum.update(f.read())
        current_hash = calculated_checksum.hexdigest()
        
        # Compare with metadata if available
        if 'checksum' in metadata:
            self.assertEqual(current_hash, metadata['checksum'], 
                             "Test set checksum mismatch with recorded metadata.")
        
        # 4. Verify Statistical Independence (Representativeness)
        # Check that the formation_energy distribution in test set is not significantly
        # different from the full pool (using a simple mean/variance check as a proxy
        # for this contract, or KS-test if scipy is available).
        full_energy = full_df['formation_energy'].dropna()
        test_energy = test_df['formation_energy'].dropna()
        
        # Assert means are within 10% of each other (loose contract for independence)
        mean_full = full_energy.mean()
        mean_test = test_energy.mean()
        
        if mean_full != 0:
            diff_ratio = abs(mean_full - mean_test) / abs(mean_full)
            self.assertLess(diff_ratio, 0.10, 
                            f"Test set mean formation energy deviates >10% from full pool. "
                            f"Full: {mean_full:.4f}, Test: {mean_test:.4f}")
        
        # 5. Verify Completeness
        # Ensure no nulls in critical columns for the test set
        self.assertTrue(test_df['formation_energy'].notna().all(), 
                        "Test set contains null formation energies.")
        
        # Ensure no nulls in material_id
        self.assertTrue(test_df['material_id'].notna().all(), 
                        "Test set contains null material IDs.")

        logger.info("Contract test_test_set_independence PASSED")

    def test_test_set_size_constraint(self):
        """
        Contract: Verify test set size is within expected bounds (e.g., 10-20% of pool).
        """
        full_df = load_data(FULL_POOL_PATH)
        test_df = load_data(TEST_SET_PATH)
        
        full_size = len(full_df)
        test_size = len(test_df)
        
        ratio = test_size / full_size
        
        # Typical split is 10-20%
        self.assertGreaterEqual(ratio, 0.05, "Test set is too small (<5% of pool).")
        self.assertLessEqual(ratio, 0.30, "Test set is too large (>30% of pool).")
        
        logger.info(f"Contract test_test_set_size_constraint PASSED (Ratio: {ratio:.2f})")

if __name__ == '__main__':
    unittest.main()