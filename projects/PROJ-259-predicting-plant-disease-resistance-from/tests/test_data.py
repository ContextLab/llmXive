"""
Contract test for data alignment in data preprocessing.
Verifies that sample IDs match exactly across modalities (SNPs and Metabolites)
as mandated by FR-001.
"""
import os
import sys
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.preprocess import align_modalities
from utils.exceptions import EX_DATA_INTEGRITY
from utils.logging import get_logger

logger = get_logger(__name__)


class TestDataAlignment:
    """Test suite for data alignment contract."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.snps_path = os.path.join(self.temp_dir, "snps.csv")
        self.metabolites_path = os.path.join(self.temp_dir, "metabolites.csv")
        self.output_path = os.path.join(self.temp_dir, "aligned.csv")
        self.exclusion_log_path = os.path.join(self.temp_dir, "exclusion_log.csv")

    def test_perfect_alignment(self):
        """Test case where all sample IDs match perfectly."""
        # Create data with matching IDs
        snps_data = pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S003'],
            'snp_1': [0, 1, 2],
            'snp_2': [1, 2, 0]
        })
        metabolites_data = pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S003'],
            'met_1': [10.5, 20.1, 15.3],
            'met_2': [5.2, 8.9, 6.1]
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        # Assert all samples retained
        assert result['total_snps'] == 3
        assert result['total_metabolites'] == 3
        assert result['aligned_count'] == 3
        assert result['excluded_count'] == 0

        # Verify output file exists and has correct content
        assert os.path.exists(self.output_path)
        aligned_df = pd.read_csv(self.output_path)
        assert len(aligned_df) == 3
        assert set(aligned_df['sample_id']) == {'S001', 'S002', 'S003'}

    def test_partial_mismatch(self):
        """Test case where some sample IDs are missing in one modality."""
        # Create data with mismatched IDs
        snps_data = pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S003', 'S004'],
            'snp_1': [0, 1, 2, 1],
            'snp_2': [1, 2, 0, 2]
        })
        metabolites_data = pd.DataFrame({
            'sample_id': ['S001', 'S002', 'S005'],  # S003, S004 missing; S005 extra
            'met_1': [10.5, 20.1, 12.0],
            'met_2': [5.2, 8.9, 7.5]
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        # Assert only matching samples retained (S001, S002)
        assert result['total_snps'] == 4
        assert result['total_metabolites'] == 3
        assert result['aligned_count'] == 2
        assert result['excluded_count'] == 3  # S003, S004 (missing met), S005 (missing snp)

        # Verify exclusion log
        assert os.path.exists(self.exclusion_log_path)
        exclusion_df = pd.read_csv(self.exclusion_log_path)
        assert len(exclusion_df) == 3
        assert set(exclusion_df['sample_id']) == {'S003', 'S004', 'S005'}
        assert 'missing_modality' in exclusion_df.columns
        assert 'timestamp' in exclusion_df.columns

    def test_no_overlap(self):
        """Test case where no sample IDs match."""
        snps_data = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'snp_1': [0, 1],
            'snp_2': [1, 2]
        })
        metabolites_data = pd.DataFrame({
            'sample_id': ['S003', 'S004'],
            'met_1': [10.5, 20.1],
            'met_2': [5.2, 8.9]
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        # Assert no samples aligned
        assert result['aligned_count'] == 0
        assert result['excluded_count'] == 4

        # Verify exclusion log contains all samples
        exclusion_df = pd.read_csv(self.exclusion_log_path)
        assert len(exclusion_df) == 4

    def test_case_sensitivity(self):
        """Test that 'S001' and 's001' are treated as different IDs (exact match)."""
        snps_data = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'snp_1': [0, 1],
            'snp_2': [1, 2]
        })
        metabolites_data = pd.DataFrame({
            'sample_id': ['s001', 'S002'],  # s001 vs S001
            'met_1': [10.5, 20.1],
            'met_2': [5.2, 8.9]
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        # Only S002 should match (exact string match required)
        assert result['aligned_count'] == 1
        assert result['excluded_count'] == 3

    def test_whitespace_handling(self):
        """Test that 'S001 ' and 'S001' are treated as different IDs."""
        snps_data = pd.DataFrame({
            'sample_id': ['S001', 'S002'],
            'snp_1': [0, 1],
            'snp_2': [1, 2]
        })
        metabolites_data = pd.DataFrame({
            'sample_id': ['S001 ', 'S002'],  # trailing space
            'met_1': [10.5, 20.1],
            'met_2': [5.2, 8.9]
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        # Only S002 should match
        assert result['aligned_count'] == 1

    def test_empty_intersection(self):
        """Test handling when intersection results in empty dataset."""
        snps_data = pd.DataFrame({
            'sample_id': [],
            'snp_1': [],
            'snp_2': []
        })
        metabolites_data = pd.DataFrame({
            'sample_id': [],
            'met_1': [],
            'met_2': []
        })

        snps_data.to_csv(self.snps_path, index=False)
        metabolites_data.to_csv(self.metabolites_path, index=False)

        # Run alignment - should not crash
        result = align_modalities(
            snps_path=self.snps_path,
            metabolites_path=self.metabolites_path,
            output_path=self.output_path,
            exclusion_log_path=self.exclusion_log_path
        )

        assert result['aligned_count'] == 0
        assert os.path.exists(self.output_path)