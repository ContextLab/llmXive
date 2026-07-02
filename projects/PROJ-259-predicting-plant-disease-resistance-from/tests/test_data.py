"""
Contract test for data alignment in T013.
Verifies matching sample IDs across modalities (SNP and Metabolite).

This test ensures that the `align_modalities` function in 
`code/data/preprocess.py` correctly:
1. Identifies common sample IDs between modalities.
2. Drops samples that do not have counterparts in both modalities.
3. Logs exclusions to `data/processed/exclusion_log.csv`.
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path
from data.preprocess import align_modalities
from data.manifest import load_manifest, ManifestLoader

# Constants for test data
TEST_SNPS = {
    'sample_001': [0, 1, 0],
    'sample_002': [1, 0, 1],
    'sample_003': [0, 0, 1],
    'sample_004': [1, 1, 0],
}

TEST_METABOLOMICS = {
    'sample_001': [10.5, 20.2],
    'sample_002': [15.1, 25.3],
    'sample_005': [12.0, 22.0],  # Mismatch: present in metabolomics, missing in SNPs
    # sample_003 and sample_004 are missing from metabolomics
}

class TestDataAlignment:
    """Test suite for contract: Data Alignment across Modalities."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """
        Setup temporary directory structure mimicking the project layout
        and inject test data files.
        """
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)

        # Create mock input files
        snp_file = self.raw_dir / "snp_matrix.csv"
        metabo_file = self.raw_dir / "metabolite_matrix.csv"

        # Write SNP data
        snp_df = pd.DataFrame.from_dict(TEST_SNPS, orient='index', columns=['snp_1', 'snp_2', 'snp_3'])
        snp_df.index.name = 'sample_id'
        snp_df.to_csv(snp_file)

        # Write Metabolomics data
        metabo_df = pd.DataFrame.from_dict(TEST_METABOLOMICS, orient='index', columns=['met_1', 'met_2'])
        metabo_df.index.name = 'sample_id'
        metabo_df.to_csv(metabo_file)

        # Create a minimal manifest for the test context
        manifest_content = """
        source_type: TEST
        files:
          snp: snp_matrix.csv
          metabolite: metabolite_matrix.csv
        """
        manifest_file = self.data_dir / "data_manifest.yaml"
        manifest_file.write_text(manifest_content)

        # Store paths for use in tests
        self.snp_path = snp_file
        self.metabo_path = metabo_file
        self.exclusion_log_path = self.processed_dir / "exclusion_log.csv"
        self.manifest_path = manifest_file

        # Mock get_path to return our temp dir
        # We cannot easily patch the module-level function, so we will 
        # pass explicit paths to align_modalities if possible, or rely on
        # the function's internal logic if it reads from manifest directly.
        # Since align_modalities expects paths or reads manifest, we pass explicit.
        
        yield

    def test_align_modalities_identifies_common_samples(self):
        """
        Verify that align_modalities correctly identifies common sample IDs.
        
        Expected common IDs: sample_001, sample_002
        Expected dropped IDs (SNP missing): sample_005
        Expected dropped IDs (Metabo missing): sample_003, sample_004
        """
        # Execute alignment
        # The function signature in preprocess.py is:
        # align_modalities(snp_path, metabo_path, exclusion_log_path)
        
        snp_df, metabo_df = align_modalities(
            self.snp_path, 
            self.metabo_path, 
            self.exclusion_log_path
        )

        # Assert indices are identical
        assert list(snp_df.index) == list(metabo_df.index), \
            "SNP and Metabolite dataframes must have identical indices after alignment."
        
        # Check specific common samples exist
        expected_common = {'sample_001', 'sample_002'}
        actual_common = set(snp_df.index)
        
        assert actual_common == expected_common, \
            f"Expected common samples {expected_common}, got {actual_common}"

    def test_align_modalities_drops_mismatched_samples(self):
        """
        Verify that samples not present in both modalities are dropped.
        """
        snp_df, metabo_df = align_modalities(
            self.snp_path, 
            self.metabo_path, 
            self.exclusion_log_path
        )

        # Ensure no mismatched samples remain
        assert 'sample_003' not in snp_df.index, "sample_003 should be dropped (missing in metabolomics)"
        assert 'sample_004' not in snp_df.index, "sample_004 should be dropped (missing in metabolomics)"
        assert 'sample_005' not in snp_df.index, "sample_005 should be dropped (missing in SNPs)"

    def test_align_modalities_logs_exclusions(self):
        """
        Verify that the exclusion log is created and contains correct entries.
        """
        align_modalities(
            self.snp_path, 
            self.metabo_path, 
            self.exclusion_log_path
        )

        # Check file exists
        assert self.exclusion_log_path.exists(), "Exclusion log file must be created."

        # Read log
        log_df = pd.read_csv(self.exclusion_log_path)
        
        # Verify columns
        expected_columns = {'sample_id', 'missing_modality', 'timestamp'}
        assert set(log_df.columns) == expected_columns, \
            f"Exclusion log must have columns {expected_columns}, got {set(log_df.columns)}"

        # Verify content
        # We expect 3 entries: sample_003, sample_004 (missing metabo), sample_005 (missing snp)
        assert len(log_df) == 3, f"Expected 3 exclusions, found {len(log_df)}"

        # Check specific missing modalities
        sample_005_row = log_df[log_df['sample_id'] == 'sample_005']
        assert len(sample_005_row) == 1, "sample_005 must be in log"
        assert sample_005_row.iloc[0]['missing_modality'] == 'snp', \
            "sample_005 is missing from SNP data"

        sample_003_row = log_df[log_df['sample_id'] == 'sample_003']
        assert len(sample_003_row) == 1, "sample_003 must be in log"
        assert sample_003_row.iloc[0]['missing_modality'] == 'metabolite', \
            "sample_003 is missing from metabolite data"

    def test_align_modalities_preserves_data_integrity(self):
        """
        Verify that the data values for kept samples are preserved correctly.
        """
        snp_df, metabo_df = align_modalities(
            self.snp_path, 
            self.metabo_path, 
            self.exclusion_log_path
        )

        # Check sample_001 values
        # SNPs: [0, 1, 0]
        # Metabo: [10.5, 20.2]
        
        assert snp_df.loc['sample_001'].tolist() == [0, 1, 0], "SNP data for sample_001 corrupted"
        assert metabo_df.loc['sample_001'].tolist() == [10.5, 20.2], "Metabolite data for sample_001 corrupted"

        # Check sample_002 values
        # SNPs: [1, 0, 1]
        # Metabo: [15.1, 25.3]
        
        assert snp_df.loc['sample_002'].tolist() == [1, 0, 1], "SNP data for sample_002 corrupted"
        assert metabo_df.loc['sample_002'].tolist() == [15.1, 25.3], "Metabolite data for sample_002 corrupted"