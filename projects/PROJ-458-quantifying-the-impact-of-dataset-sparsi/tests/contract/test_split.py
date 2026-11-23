"""
Contract tests for test_split.py module.
Verifies that the test set generation adheres to strict independence and
data hygiene contracts defined in the project specifications.
"""

import os
import sys
import json
import pytest
import hashlib
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running from tests/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from test_split import load_data, create_test_set, save_test_set, save_indices, save_metadata, main
from utils.contract_validator import validate_contract
from utils.logging import get_logger

logger = get_logger(__name__)


class TestTestSetIndependence:
    """
    Contract Test: test_test_set_independence
    Verifies that the test set is strictly disjoint from the training pool
    and that stratification is preserved.
    """

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        """Setup temporary paths for test artifacts if real files don't exist."""
        self.raw_pool_path = project_root / "data" / "raw" / "raw_pool.csv"
        self.test_set_path = project_root / "data" / "processed" / "test_set.csv"
        self.test_indices_path = project_root / "data" / "processed" / "test_set_indices.csv"
        self.metadata_path = project_root / "data" / "metadata" / "test_set_metadata.json"
        
        # Check if prerequisite files exist
        if not self.raw_pool_path.exists():
            pytest.skip(
                f"Prerequisite file {self.raw_pool_path} not found. "
                "Run T024 to generate raw_pool.csv before running this contract test."
            )

    def test_test_set_independence(self):
        """
        Contract: The test set must be a strict subset of the raw pool,
        and the indices must not overlap with any future training pool indices.
        
        Specifically:
        1. All rows in test_set.csv must exist in raw_pool.csv.
        2. The indices in test_set_indices.csv must be unique and valid.
        3. The formation_energy distribution in the test set must match the 
           stratification logic (quantile bins) used during creation.
        """
        # Load raw data
        raw_df = load_data(self.raw_pool_path)
        
        # Simulate the split logic to ensure contract holds
        # We use a fixed seed to ensure reproducibility in the test
        target_size = 5000
        seed = 42
        
        # Run the split logic
        test_df, test_indices = create_test_set(raw_df, target_size, seed)
        
        # Contract 1: Verify all test rows exist in raw pool
        # We check by material_id and formation_energy to handle potential index shifts
        raw_ids = set(zip(raw_df['material_id'], raw_df['formation_energy']))
        test_ids = set(zip(test_df['material_id'], test_df['formation_energy']))
        
        assert test_ids.issubset(raw_ids), \
            "Contract Failed: Test set contains entries not present in the raw pool."
        
        # Contract 2: Verify indices are within bounds and unique
        assert len(test_indices) == len(set(test_indices)), \
            "Contract Failed: Test set indices contain duplicates."
        assert all(0 <= idx < len(raw_df) for idx in test_indices), \
            "Contract Failed: Test set indices are out of bounds for the raw pool."
        
        # Contract 3: Verify Stratification (Quantile Bins)
        # The test set should have a similar distribution of formation_energy bins
        # as the raw pool, within a tolerance (e.g., 5% deviation per bin)
        n_bins = 10
        raw_bins = pd.qcut(raw_df['formation_energy'].dropna(), q=n_bins, labels=False)
        test_bins = pd.qcut(test_df['formation_energy'].dropna(), q=n_bins, labels=False)
        
        raw_dist = raw_bins.value_counts(normalize=True).sort_index()
        test_dist = test_bins.value_counts(normalize=True).sort_index()
        
        # Align indices (some bins might be missing in test if size is small, though 5000 is large)
        all_bins = sorted(set(raw_dist.index) | set(test_dist.index))
        
        for bin_idx in all_bins:
            raw_pct = raw_dist.get(bin_idx, 0.0)
            test_pct = test_dist.get(bin_idx, 0.0)
            
            deviation = abs(raw_pct - test_pct)
            assert deviation < 0.05, \
                f"Contract Failed: Stratification deviation in bin {bin_idx} " \
                f"({deviation:.2%}) exceeds 5% threshold. Raw: {raw_pct:.2%}, Test: {test_pct:.2%}"
        
        logger.info("Contract Test 'test_test_set_independence' PASSED.")

    def test_test_set_metadata_integrity(self):
        """
        Contract: The metadata file must accurately reflect the test set's
        properties (row count, checksum) and be consistent with the CSV.
        """
        if not self.metadata_path.exists():
            # If metadata doesn't exist, generate it first to test the generation logic
            raw_df = load_data(self.raw_pool_path)
            test_df, test_indices = create_test_set(raw_df, 5000, 42)
            save_test_set(test_df, self.test_set_path)
            save_indices(test_indices, self.test_indices_path)
            save_metadata(test_df, self.metadata_path)
        
        # Load metadata
        with open(self.metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Load actual test set
        test_df = pd.read_csv(self.test_set_path)
        
        # Contract 4: Row count matches
        assert metadata['row_count'] == len(test_df), \
            "Contract Failed: Metadata row_count does not match actual test set rows."
        
        # Contract 5: Checksum matches
        # Calculate checksum of the actual file content
        file_hash = hashlib.sha256()
        with open(self.test_set_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        actual_checksum = file_hash.hexdigest()
        
        assert metadata['checksum'] == actual_checksum, \
            "Contract Failed: Metadata checksum does not match actual file checksum."
        
        logger.info("Contract Test 'test_test_set_metadata_integrity' PASSED.")

    def test_no_data_leakage_from_future_pools(self):
        """
        Contract: Ensure that the test set indices are explicitly excluded
        from any subsequent training pool generation logic.
        
        This verifies that if a training pool were to be generated from
        the remaining raw pool, it would not contain any test set entries.
        """
        raw_df = load_data(self.raw_pool_path)
        test_df, test_indices = create_test_set(raw_df, 5000, 42)
        
        # Simulate the "remaining" pool
        remaining_indices = [i for i in range(len(raw_df)) if i not in test_indices]
        remaining_df = raw_df.iloc[remaining_indices]
        
        # Contract 6: Intersection of test and remaining IDs must be empty
        test_ids = set(test_df['material_id'])
        remaining_ids = set(remaining_df['material_id'])
        
        intersection = test_ids.intersection(remaining_ids)
        assert len(intersection) == 0, \
            f"Contract Failed: Data leakage detected. {len(intersection)} IDs " \
            "exist in both test set and remaining training pool."
        
        logger.info("Contract Test 'test_no_data_leakage_from_future_pools' PASSED.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])