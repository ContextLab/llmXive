import os
import csv
import tempfile
import unittest
from unittest.mock import patch

# Import the processing function from the project
from data.ingestion import process_dataset, calculate_mw

class TestIngestionCleaning(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raw_csv_path = os.path.join(self.temp_dir.name, "polymer_raw.csv")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('data.ingestion.calculate_mw')
    def test_cleaning_and_review_log(self, mock_mw):
        """
        Verify that:
        - Entries with MW < 1000 are excluded and logged.
        - Duplicate entries with high variance are flagged for review.
        - Duplicate entries with low variance are averaged.
        - Review log CSV is created with correct entries.
        """
        # Mock molecular weight: return high weight for SMILES starting with "HIGH"
        def mw_side_effect(smiles):
            if smiles.startswith("HIGH"):
                return 1500.0
            return 500.0  # low weight for everything else

        mock_mw.side_effect = mw_side_effect

        # Construct synthetic raw data
        raw_data = [
            # Low MW (should be excluded)
            {"smiles": "LOW1", "permeability_log": -5.0},
            # High MW, first occurrence
            {"smiles": "HIGH_A", "permeability_log": -6.0},
            # Duplicate with low variance (should be averaged)
            {"smiles": "HIGH_A", "permeability_log": -6.3},
            # Duplicate with high variance (should be flagged)
            {"smiles": "HIGH_B", "permeability_log": -4.0},
            {"smiles": "HIGH_B", "permeability_log": -5.0},
            # Missing permeability (should be skipped)
            {"smiles": "HIGH_C"},
            # Missing SMILES (should be skipped)
            {"permeability_log": -7.0},
        ]

        # Run processing
        graphs, records, excluded = process_dataset(raw_data, self.raw_csv_path)

        # Verify that low MW entry was excluded
        self.assertNotIn("LOW1", [r.smiles for r in records])
        self.assertIn("LOW1", excluded)

        # Verify that HIGH_A appears once with averaged permeability
        high_a_records = [r for r in records if r.smiles == "HIGH_A"]
        self.assertEqual(len(high_a_records), 1)
        expected_avg = (-6.0 + -6.3) / 2
        self.assertAlmostEqual(high_a_records[0].permeability_log, expected_avg, places=6)

        # Verify that HIGH_B was excluded due to high variance
        self.assertNotIn("HIGH_B", [r.smiles for r in records])
        self.assertIn("HIGH_B", excluded)

        # Verify that review log file exists and contains correct rows
        review_log_path = os.path.join(os.path.dirname(self.raw_csv_path), "review_log.csv")
        self.assertTrue(os.path.isfile(review_log_path))

        with open(review_log_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Expected review entries:
        # - LOW1 excluded due to MW
        # - HIGH_B flagged conflict
        # - HIGH_A duplicate low variance should NOT appear in review log
        # - HIGH_C missing permeability should not be logged (per spec)
        expected = {
            ("LOW1", "EXCLUDED", "MW < 1000 Da"),
            ("HIGH_B", "FLAGGED_CONFLICT", "High variance in duplicate values")
        }

        actual = {(row["smiles"], row["status"], row["reason"]) for row in rows}
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()