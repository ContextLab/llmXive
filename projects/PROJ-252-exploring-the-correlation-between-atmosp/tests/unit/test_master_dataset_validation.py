"""
Verification test for T017: Master Dataset Validation.

This test asserts that:
1. The file `data/processed/master_dataset.csv` exists.
2. The row count matches `data/processed/config.yaml` `expected_earthquake_count` (12) within 1% tolerance.
3. The schema matches the required fields defined in the contracts.
"""
import os
import sys
import unittest
import yaml
import pandas as pd
from pathlib import Path

# Add code directory to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

class TestMasterDatasetValidation(unittest.TestCase):
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_path = self.project_root / "data" / "processed" / "config.yaml"
        self.dataset_path = self.project_root / "data" / "processed" / "master_dataset.csv"
        
        # Load configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.expected_count = int(self.config.get('expected_earthquake_count', 12))
        
        # Define required columns based on schema contracts (earthquake + pressure anomaly)
        self.required_columns = {
            'event_id', 'magnitude', 'depth', 'lat', 'lon', 'timestamp',
            'pressure_value', 'anomaly_value', 'window_type', 'checksum'
        }

    def test_dataset_file_exists(self):
        """Assert that the master dataset file exists."""
        self.assertTrue(
            self.dataset_path.exists(), 
            f"Master dataset file not found at {self.dataset_path}"
        )

    def test_row_count_tolerance(self):
        """Assert row count matches expected count within 1% tolerance."""
        df = pd.read_csv(self.dataset_path)
        actual_count = len(df)
        
        tolerance = 0.01
        lower_bound = self.expected_count * (1 - tolerance)
        upper_bound = self.expected_count * (1 + tolerance)
        
        self.assertGreaterEqual(
            actual_count, lower_bound,
            f"Row count {actual_count} is below lower bound {lower_bound} (expected {self.expected_count})"
        )
        self.assertLessEqual(
            actual_count, upper_bound,
            f"Row count {actual_count} is above upper bound {upper_bound} (expected {self.expected_count})"
        )

    def test_schema_compliance(self):
        """Assert that all required columns are present in the dataset."""
        if not self.dataset_path.exists():
            self.skipTest("Dataset file does not exist yet")
        
        df = pd.read_csv(self.dataset_path)
        actual_columns = set(df.columns)
        
        missing_columns = self.required_columns - actual_columns
        
        self.assertEqual(
            len(missing_columns), 0,
            f"Missing required columns: {missing_columns}. Found: {actual_columns}"
        )

    def test_data_integrity_checksum_file_exists(self):
        """Assert that the checksum file exists for T017 verification."""
        checksum_path = self.dataset_path.with_suffix('.csv.sha256')
        self.assertTrue(
            checksum_path.exists(),
            f"Checksum file not found at {checksum_path}"
        )

if __name__ == '__main__':
    unittest.main()