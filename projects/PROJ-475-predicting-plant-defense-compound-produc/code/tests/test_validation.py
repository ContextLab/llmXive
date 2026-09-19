"""
Integration tests for the validation pipeline (Task T017).

Specific Tests:
- test_merge_preserves_population_ids: Verifies that merge_datasets correctly joins on population_id.
- test_listwise_deletion_removes_nulls: Verifies that perform_listwise_deletion removes rows with missing data.
- test_retention_check_fails_below_80_percent: Verifies that calculate_retention_percentage raises SystemExit with E-DATA-INSUFFICIENT if retention < 80%.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest
import pandas as pd

# Adjust imports based on project structure
# Assuming tests are in code/tests/ and modules are in code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.validation import (
    merge_datasets,
    perform_listwise_deletion,
    calculate_retention_percentage,
    load_json_data,
    load_vcf_as_dataframe
)
from utils.io import DiskSpaceError


class TestValidationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.logs_dir = self.data_dir / "logs"

        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.logs_dir.mkdir()

        # Create dummy log file
        self.exclusions_log = self.logs_dir / "exclusions.log"
        self.exclusions_log.touch()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def _create_mock_genomic_vcf(self, file_path, population_ids):
        """Create a mock VCF file for testing."""
        # Minimal VCF header and some dummy data
        header_lines = [
            "##fileformat=VCFv4.2",
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(population_ids)
        ]
        rows = []
        for i, pid in enumerate(population_ids):
            # Simple genotype: 0/0 for all
            gt = "0/0"
            row = f"chr1\t100\t.\tA\tT\t30\tPASS\t.\tGT\t{gt}"
            rows.append(row)

        content = "\n".join(header_lines + rows)
        with open(file_path, "w") as f:
            f.write(content)

    def _create_mock_env_csv(self, file_path, population_ids):
        """Create a mock Environmental CSV file."""
        data = {
            "population_id": population_ids,
            "lat": [30.0] * len(population_ids),
            "lon": [40.0] * len(population_ids),
            "temp": [20.0] * len(population_ids),
            "precip": [500.0] * len(population_ids),
            "ph": [6.5] * len(population_ids)
        }
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)

    def _create_mock_compounds_json(self, file_path, population_ids):
        """Create a mock Compound JSON file."""
        data = []
        for pid in population_ids:
            data.append({
                "population_id": pid,
                "compound_name": "Alkaloid_A",
                "concentration": 10.5,
                "source_study": "Study_X"
            })
        with open(file_path, "w") as f:
            json.dump(data, f)

    def test_merge_preserves_population_ids(self):
        """
        Test that merge_datasets correctly joins datasets on population_id
        and preserves all expected population IDs.
        """
        # Setup: Create raw files with known population IDs
        population_ids = ["POP_001", "POP_002", "POP_003", "POP_004", "POP_005"]
        genomic_path = self.raw_dir / "genomic.vcf"
        env_path = self.raw_dir / "env_data.csv"
        compound_path = self.raw_dir / "compound_data.json"

        self._create_mock_genomic_vcf(genomic_path, population_ids)
        self._create_mock_env_csv(env_path, population_ids)
        self._create_mock_compounds_json(compound_path, population_ids)

        # Execute: Merge datasets
        output_path = self.processed_dir / "merged_raw.csv"
        try:
            # We need to mock the logging to avoid file path issues in tests if needed,
            # but the function should work with the paths provided.
            # The function signature expects paths or DataFrames. Based on T013 description:
            # "Input: Raw files from T010-T012. Logic: Perform inner join..."
            # We assume merge_datasets takes file paths.
            merge_datasets(
                genomic_file=str(genomic_path),
                env_file=str(env_path),
                compound_file=str(compound_path),
                output_file=str(output_path)
            )
        except Exception as e:
            self.fail(f"merge_datasets failed with: {e}")

        # Verify: Check output file exists and contains correct IDs
        self.assertTrue(output_path.exists(), "Merged output file was not created.")

        df = pd.read_csv(output_path)
        self.assertIn("population_id", df.columns, "population_id column missing in merged data.")

        # Since it's an inner join on all three, and we provided same IDs for all,
        # all 5 should be present.
        present_ids = set(df["population_id"].tolist())
        expected_ids = set(population_ids)

        self.assertEqual(present_ids, expected_ids,
                         f"Merged data population IDs {present_ids} do not match expected {expected_ids}")

    def test_listwise_deletion_removes_nulls(self):
        """
        Test that perform_listwise_deletion removes rows with missing data
        in key columns (Genomic, Env, Compound).
        """
        # Setup: Create a DataFrame with intentional nulls
        # Simulate the state after merge (some rows might have nulls if join was outer or data was missing)
        data = {
            "population_id": ["POP_001", "POP_002", "POP_003", "POP_004"],
            "lat": [30.0, 31.0, None, 33.0], # Null in POP_003
            "temp": [20.0, 21.0, 22.0, 23.0],
            "concentration": [10.0, None, 12.0, 13.0], # Null in POP_002
            "genotype_score": [0.5, 0.6, 0.7, None] # Null in POP_004 (simulating missing genomic)
        }
        df_input = pd.DataFrame(data)
        input_path = self.processed_dir / "merged_raw_with_nulls.csv"
        output_path = self.processed_dir / "final_cleaned.csv"

        df_input.to_csv(input_path, index=False)

        # Execute: Perform listwise deletion
        try:
            perform_listwise_deletion(
                input_file=str(input_path),
                output_file=str(output_path),
                log_file=str(self.exclusions_log)
            )
        except Exception as e:
            self.fail(f"perform_listwise_deletion failed with: {e}")

        # Verify: Output file exists and has no nulls in key columns
        self.assertTrue(output_path.exists(), "Cleaned output file was not created.")

        df_clean = pd.read_csv(output_path)

        # Check that rows with nulls in key columns are removed
        # Key columns to check: lat, concentration, genotype_score (and population_id)
        # The function should remove any row where ANY of these are null (listwise deletion)
        self.assertEqual(len(df_clean), 1, "Expected only 1 row (POP_001) after listwise deletion.")

        # Verify the remaining row is POP_001
        self.assertEqual(df_clean.iloc[0]["population_id"], "POP_001")

        # Verify no nulls in the remaining data
        self.assertFalse(df_clean.isnull().any().any(), "Remaining data contains nulls.")

    def test_retention_check_fails_below_80_percent(self):
        """
        Test that calculate_retention_percentage raises SystemExit with E-DATA-INSUFFICIENT
        if retention is below 80%.
        """
        # Setup: Define initial and final counts
        initial_count = 100
        final_count = 79 # 79% retention

        # Execute: Call the function
        with self.assertRaises(SystemExit) as context:
            calculate_retention_percentage(
                n_initial=initial_count,
                n_final=final_count,
                threshold=80.0,
                error_code="E-DATA-INSUFFICIENT"
            )

        # Verify: Check exit code and message
        self.assertEqual(context.exception.code, "E-DATA-INSUFFICIENT",
                         f"Expected exit code 'E-DATA-INSUFFICIENT', got {context.exception.code}")

        # Also test that it does NOT fail when above threshold
        final_count_ok = 85 # 85% retention
        try:
            calculate_retention_percentage(
                n_initial=initial_count,
                n_final=final_count_ok,
                threshold=80.0,
                error_code="E-DATA-INSUFFICIENT"
            )
        except SystemExit:
            self.fail("calculate_retention_percentage should not raise SystemExit when retention >= threshold")

    def test_retention_check_passes_at_80_percent(self):
        """
        Test that calculate_retention_percentage passes exactly at 80% threshold.
        """
        initial_count = 100
        final_count = 80 # Exactly 80%

        try:
            calculate_retention_percentage(
                n_initial=initial_count,
                n_final=final_count,
                threshold=80.0,
                error_code="E-DATA-INSUFFICIENT"
            )
        except SystemExit:
            self.fail("calculate_retention_percentage should not raise SystemExit when retention == threshold")

    def test_listwise_deletion_logs_exclusions(self):
        """
        Test that perform_listwise_deletion logs excluded population IDs to the log file.
        """
        # Setup: Create a DataFrame with nulls
        data = {
            "population_id": ["POP_001", "POP_002", "POP_003"],
            "lat": [30.0, None, 32.0],
            "temp": [20.0, 21.0, 22.0],
            "concentration": [10.0, 11.0, None]
        }
        df_input = pd.DataFrame(data)
        input_path = self.processed_dir / "merged_log_test.csv"
        output_path = self.processed_dir / "cleaned_log_test.csv"

        df_input.to_csv(input_path, index=False)

        # Execute
        perform_listwise_deletion(
            input_file=str(input_path),
            output_file=str(output_path),
            log_file=str(self.exclusions_log)
        )

        # Verify log content
        self.assertTrue(self.exclusions_log.exists(), "Exclusions log file was not created.")

        with open(self.exclusions_log, "r") as f:
            log_content = f.read()

        # Should mention POP_002 and POP_003 (the ones with nulls)
        # The exact format depends on the implementation, but we expect some record of exclusion
        self.assertIn("POP_002", log_content, "POP_002 should be logged as excluded.")
        self.assertIn("POP_003", log_content, "POP_003 should be logged as excluded.")