"""
Integration tests for the validation pipeline (T013, T014, T015).
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.validation import (
    merge_datasets, 
    perform_listwise_deletion, 
    validate_data_integrity,
    calculate_retention_percentage,
    merge_and_validate,
    run_validation_pipeline,
    LOG_EXCLUSIONS
)
from utils.logging import configure_root_logger


class TestValidationPipelineIntegration(unittest.TestCase):
    """Integration tests for T013, T014, T015."""

    def setUp(self):
        """Set up temporary directories and mock data."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir()
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir()
        self.logs_dir = Path(self.test_dir) / "logs"
        self.logs_dir.mkdir()

        # Mock data
        self.genomic_data = pd.DataFrame({
            'population_id': ['P1', 'P2', 'P3'],
            'chrom': ['chr1', 'chr1', 'chr2'],
            'pos': [100, 200, 300]
        })
        
        self.env_data = pd.DataFrame({
            'population_id': ['P1', 'P2', 'P4'], # P4 missing in genomic, P3 missing in env
            'lat': [1.0, 2.0, 3.0],
            'lon': [1.0, 2.0, 3.0],
            'temp': [20.0, 21.0, 22.0],
            'precip': [100.0, 110.0, 120.0],
            'ph': [6.5, 6.6, 6.7]
        })
        
        self.compound_data = [
            {'population_id': 'P1', 'compound_name': 'C1', 'concentration': 10.0, 'source_study': 'S1'},
            {'population_id': 'P2', 'compound_name': 'C2', 'concentration': 20.0, 'source_study': 'S2'},
            {'population_id': 'P5', 'compound_name': 'C3', 'concentration': 30.0, 'source_study': 'S3'} # P5 missing in others
        ]

        # Write mock files
        self.genomic_path = self.raw_dir / "genomic.vcf"
        # Write a simplified VCF-like file for testing
        with open(self.genomic_path, 'w') as f:
            f.write("##fileformat=VCFv4.2\n")
            f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tSAMPLE1\n")
            for _, row in self.genomic_data.iterrows():
                f.write(f"{row['chrom']}\t{row['pos']}\t.\tA\tT\t.\t.\tpopulation_id={row['population_id']}\t0/1\n")

        self.env_path = self.raw_dir / "env_data.csv"
        self.env_data.to_csv(self.env_path, index=False)

        self.compound_path = self.raw_dir / "compound_data.json"
        with open(self.compound_path, 'w') as f:
            json.dump(self.compound_data, f)

        # Set paths for testing
        self.output_merged = self.processed_dir / "merged_raw.csv"
        self.output_cleaned = self.processed_dir / "final_cleaned.csv"
        self.log_path = self.logs_dir / "exclusions.log"

    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)

    def test_merge_preserves_population_ids(self):
        """Test that merge_datasets preserves population_id and performs inner join."""
        # Load data manually for this test
        genomic_df = self.genomic_data
        env_df = self.env_data
        compound_df = pd.DataFrame(self.compound_data)

        merged = merge_datasets(genomic_df, env_df, compound_df)

        # Expected: Only P1 and P2 are in all three
        # P3 missing in env, P4 missing in genomic, P5 missing in genomic/env
        expected_pops = ['P1', 'P2']
        self.assertEqual(set(merged['population_id'].unique()), set(expected_pops))
        
        # Check source_study is preserved
        self.assertIn('source_study', merged.columns)

    def test_listwise_deletion_removes_nulls(self):
        """Test that perform_listwise_deletion removes rows with nulls."""
        # Create a merged dataset with some nulls
        merged_data = pd.DataFrame({
            'population_id': ['P1', 'P2', 'P3'],
            'lat': [1.0, None, 3.0],
            'temp': [20.0, 21.0, None],
            'concentration': [10.0, 20.0, 30.0]
        })
        
        # Save to a temp file
        temp_merged = Path(self.test_dir) / "temp_merged.csv"
        merged_data.to_csv(temp_merged, index=False)
        
        temp_cleaned = Path(self.test_dir) / "temp_cleaned.csv"
        
        cleaned = perform_listwise_deletion(temp_merged, temp_cleaned)
        
        # Only P1 should remain (no nulls)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned['population_id'].iloc[0], 'P1')
        
        # Check file was written
        self.assertTrue(temp_cleaned.exists())

    def test_retention_check_logic(self):
        """Test retention percentage calculation."""
        # 80% threshold
        initial = 100
        final = 80
        self.assertEqual(calculate_retention_percentage(initial, final), 80.0)
        
        final = 79
        self.assertLess(calculate_retention_percentage(initial, final), 80.0)
        
        final = 81
        self.assertGreater(calculate_retention_percentage(initial, final), 80.0)

    def test_integration_pipeline(self):
        """Test the full pipeline with mock data."""
        # We need to patch the paths in the module
        # For simplicity, we test the individual functions with our temp files
        
        # 1. Merge
        merged = merge_and_validate(
            genomic_path=self.genomic_path,
            env_path=self.env_path,
            compound_path=self.compound_path,
            output_path=self.output_merged
        )
        
        # Verify merged file exists
        self.assertTrue(self.output_merged.exists())
        
        # 2. Listwise Deletion
        cleaned = perform_listwise_deletion(
            input_path=self.output_merged,
            output_path=self.output_cleaned
        )
        
        # Verify cleaned file exists
        self.assertTrue(self.output_cleaned.exists())
        
        # 3. Validate
        self.assertTrue(validate_data_integrity(cleaned))
        
        # Check exclusions log
        if self.log_path.exists():
            with open(self.log_path, 'r') as f:
                content = f.read()
                self.assertIn("Excluded populations", content)


if __name__ == "__main__":
    configure_root_logger()
    unittest.main()
