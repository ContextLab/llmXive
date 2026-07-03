"""
Unit tests for edge cases in the mitochondrial aging analysis pipeline.

Tests cover:
- Zero heteroplasmy burden scenarios
- Missing haplogroup assignments
- Empty datasets
- Boundary conditions for age and depth
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.preprocess import calculate_burden_per_sample, assign_haplogroups
from analysis.merge_metadata import merge_datasets
from analysis.model import calculate_unadjusted_spearman, calculate_rank_ols


class TestZeroBurdenScenarios:
    """Tests for samples with zero heteroplasmy burden."""

    def test_zero_burden_calculation(self):
        """Test that samples with no variants get zero burden."""
        # Create a mock VCF-like dataframe with no variants for a sample
        data = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S1', 'S2'],
            'VAF': [0.0, 0.0, 0.0],
            'FILTER': ['PASS', 'PASS', 'PASS'],
            'CHROM': ['chrM', 'chrM', 'chrM'],
            'DEPTH': [100, 100, 100]
        })
        
        # Filter for PASS and chrM (already done in data)
        filtered = data[(data['FILTER'] == 'PASS') & (data['CHROM'] == 'chrM')]
        
        # Calculate burden per sample
        result = calculate_burden_per_sample(filtered, threshold=0.01)
        
        # Both samples should have zero burden
        assert result.loc[result['SAMPLE_ID'] == 'S1', 'BURDEN'].values[0] == 0.0
        assert result.loc[result['SAMPLE_ID'] == 'S2', 'BURDEN'].values[0] == 0.0

    def test_zero_burden_correlation(self):
        """Test correlation calculation with zero burden values."""
        # Create dataset with some zero burden values
        data = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.0, 0.0, 0.05, 0.1, 0.15],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Should not raise an error
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        assert not np.isnan(corr)
        assert not np.isnan(pval)

    def test_all_zero_burden(self):
        """Test when all samples have zero burden."""
        data = pd.DataFrame({
            'age': [20, 30, 40, 50, 60],
            'burden': [0.0, 0.0, 0.0, 0.0, 0.0],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Should handle gracefully
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        # Correlation should be 0 (or undefined, but not crash)
        assert not np.isnan(pval)


class TestMissingHaplogroupScenarios:
    """Tests for samples with missing haplogroup assignments."""

    def test_missing_haplogroup_in_merge(self):
        """Test that samples with missing haplogroups are handled correctly."""
        # Create burden data
        burden_df = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S2', 'S3', 'S4'],
            'BURDEN': [0.05, 0.1, 0.15, 0.2]
        })
        
        # Create haplogroup data with one missing
        haplo_df = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S2', 'S3'],  # S4 missing
            'HAPLOGROUP': ['H1', 'J2', 'U5']
        })
        
        # Create metadata
        metadata_df = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S2', 'S3', 'S4'],
            'age': [25, 35, 45, 55],
            'sex': ['M', 'F', 'M', 'F'],
            'population': ['EUR', 'AFR', 'EAS', 'SAS']
        })
        
        # Perform merge
        merged = merge_datasets(burden_df, haplo_df, metadata_df)
        
        # S4 should have NaN for haplogroup
        assert pd.isna(merged.loc[merged['SAMPLE_ID'] == 'S4', 'HAPLOGROUP'].values[0])
        
        # S1, S2, S3 should have valid haplogroups
        assert merged.loc[merged['SAMPLE_ID'] == 'S1', 'HAPLOGROUP'].values[0] == 'H1'
        assert merged.loc[merged['SAMPLE_ID'] == 'S2', 'HAPLOGROUP'].values[0] == 'J2'
        assert merged.loc[merged['SAMPLE_ID'] == 'S3', 'HAPLOGROUP'].values[0] == 'U5'

    def test_all_missing_haplogroups(self):
        """Test when all haplogroup assignments fail."""
        burden_df = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S2'],
            'BURDEN': [0.05, 0.1]
        })
        
        # Empty haplogroup dataframe
        haplo_df = pd.DataFrame(columns=['SAMPLE_ID', 'HAPLOGROUP'])
        
        metadata_df = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S2'],
            'age': [25, 35],
            'sex': ['M', 'F'],
            'population': ['EUR', 'AFR']
        })
        
        merged = merge_datasets(burden_df, haplo_df, metadata_df)
        
        # All should have NaN haplogroups
        assert all(pd.isna(merged['HAPLOGROUP']))

    def test_haplogroup_assignment_failure(self):
        """Test handling of haplogroup assignment failures."""
        # Create a mock VCF file content that would cause haplogrep to fail
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False) as f:
            f.write("##fileformat=VCFv4.2\n")
            f.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n")
            f.write("chrM\t100\t.\tA\tG\t30\tPASS\t.\tGT:DP\t0/1:100\n")
            temp_vcf = f.name
        
        try:
            # Mock haplogrep2 to return failure
            with patch('analysis.preprocess.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock()
                mock_run.return_value.stdout = ""  # Empty output means failure
                mock_run.return_value.returncode = 1
                
                # This should not crash
                result = assign_haplogroups(temp_vcf)
                
                # Result should be empty or have NaN values
                if len(result) > 0:
                    assert all(pd.isna(result['HAPLOGROUP']))
        finally:
            os.unlink(temp_vcf)


class TestEmptyDatasetScenarios:
    """Tests for empty datasets and edge cases."""

    def test_empty_dataframe_operations(self):
        """Test that operations handle empty dataframes gracefully."""
        empty_df = pd.DataFrame(columns=['age', 'burden', 'sex', 'PC1', 'PC2'])
        
        # Should not crash
        corr, pval = calculate_unadjusted_spearman(empty_df, 'burden', 'age')
        
        # Should return NaN for empty data
        assert np.isnan(corr)
        assert np.isnan(pval)

    def test_single_sample(self):
        """Test with only one sample."""
        data = pd.DataFrame({
            'age': [40],
            'burden': [0.1],
            'sex': ['M'],
            'PC1': [0.3],
            'PC2': [0.3]
        })
        
        # Correlation with single sample is undefined
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        assert np.isnan(corr)
        assert np.isnan(pval)

    def test_two_samples(self):
        """Test with exactly two samples."""
        data = pd.DataFrame({
            'age': [20, 60],
            'burden': [0.0, 0.2],
            'sex': ['M', 'F'],
            'PC1': [0.1, 0.5],
            'PC2': [0.1, 0.5]
        })
        
        # Should calculate correlation
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        assert not np.isnan(corr)
        assert not np.isnan(pval)


class TestBoundaryConditions:
    """Tests for boundary values and edge conditions."""

    def test_extreme_age_values(self):
        """Test with very young and very old ages."""
        data = pd.DataFrame({
            'age': [0, 100, 105],  # Including extreme values
            'burden': [0.0, 0.15, 0.18],
            'sex': ['M', 'F', 'M'],
            'PC1': [0.1, 0.5, 0.6],
            'PC2': [0.1, 0.5, 0.6]
        })
        
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        assert not np.isnan(corr)
        assert not np.isnan(pval)

    def test_extreme_depth_values(self):
        """Test with very low and very high sequencing depth."""
        data = pd.DataFrame({
            'age': [30, 40, 50],
            'burden': [0.05, 0.1, 0.15],
            'depth': [10, 500, 1000],  # Extreme depth values
            'sex': ['M', 'F', 'M'],
            'PC1': [0.1, 0.3, 0.5],
            'PC2': [0.1, 0.3, 0.5]
        })
        
        # Should handle extreme depth values
        model_results = calculate_rank_ols(data)
        
        assert model_results is not None
        assert 'coefficient' in model_results.columns or len(model_results) > 0

    def test_threshold_edge_cases(self):
        """Test burden calculation at threshold boundaries."""
        data = pd.DataFrame({
            'SAMPLE_ID': ['S1', 'S1', 'S1', 'S1'],
            'VAF': [0.009, 0.01, 0.011, 0.02],  # Around 1% threshold
            'FILTER': ['PASS', 'PASS', 'PASS', 'PASS'],
            'CHROM': ['chrM', 'chrM', 'chrM', 'chrM'],
            'DEPTH': [100, 100, 100, 100]
        })
        
        # At 1% threshold, only VAF >= 0.01 should count
        filtered = data[(data['FILTER'] == 'PASS') & (data['CHROM'] == 'chrM')]
        result = calculate_burden_per_sample(filtered, threshold=0.01)
        
        # Should have 3 variants counted (0.01, 0.011, 0.02)
        assert result.loc[result['SAMPLE_ID'] == 'S1', 'BURDEN'].values[0] == 3

    def test_missing_values_in_critical_columns(self):
        """Test handling of missing values in critical columns."""
        data = pd.DataFrame({
            'age': [20, np.nan, 40, 50],
            'burden': [0.05, 0.1, np.nan, 0.2],
            'sex': ['M', 'F', 'M', np.nan],
            'PC1': [0.1, 0.2, 0.3, 0.4],
            'PC2': [0.1, 0.2, 0.3, 0.4]
        })
        
        # Should handle missing values gracefully
        corr, pval = calculate_unadjusted_spearman(data, 'burden', 'age')
        
        # Should not crash, though correlation may be based on fewer samples
        assert not np.isnan(pval)

class TestRankTransformationEdgeCases:
    """Tests for rank transformation edge cases in Rank-OLS."""

    def test_tied_ranks(self):
        """Test handling of tied values in rank transformation."""
        data = pd.DataFrame({
            'age': [20, 20, 30, 30, 40],  # Tied values
            'burden': [0.05, 0.05, 0.1, 0.1, 0.15],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Should handle tied ranks without error
        model_results = calculate_rank_ols(data)
        
        assert model_results is not None
        assert len(model_results) > 0

    def test_constant_variable(self):
        """Test when a variable has constant values."""
        data = pd.DataFrame({
            'age': [30, 30, 30, 30, 30],  # Constant age
            'burden': [0.05, 0.1, 0.15, 0.2, 0.25],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        
        # Should handle constant variable (rank will be all same)
        model_results = calculate_rank_ols(data)
        
        # Should not crash, though results may be degenerate
        assert model_results is not None

if __name__ == '__main__':
    pytest.main([__file__, '-v'])