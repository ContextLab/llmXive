"""
Unit tests for preprocessing functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import (
    match_accessions,
    filter_missingness,
    encode_genotypes
)

class TestAccessionMatching:
    def test_match_accessions_basic(self):
        """Test basic accession matching functionality."""
        genomic = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'chr1': [0, 1, 2]
        })
        phenotypic = pd.DataFrame({
            'accession': ['B', 'C', 'D'],
            'root_length': [10, 20, 30]
        })
        
        matched_gen, matched_pheno, excluded = match_accessions(genomic, phenotypic)
        
        assert len(matched_gen) == 2
        assert len(matched_pheno) == 2
        assert set(matched_gen['accession']) == {'B', 'C'}
        assert 'A' in excluded['genomic']
        assert 'D' in excluded['phenotypic']

    def test_no_common_accessions(self):
        """Test when there are no common accessions."""
        genomic = pd.DataFrame({
            'accession': ['A', 'B'],
            'chr1': [0, 1]
        })
        phenotypic = pd.DataFrame({
            'accession': ['C', 'D'],
            'root_length': [10, 20]
        })
        
        matched_gen, matched_pheno, excluded = match_accessions(genomic, phenotypic)
        
        assert len(matched_gen) == 0
        assert len(matched_pheno) == 0
        assert set(excluded['genomic']) == {'A', 'B'}
        assert set(excluded['phenotypic']) == {'C', 'D'}

class TestMissingnessFilter:
    def test_filter_missingness_basic(self):
        """Test basic missingness filtering."""
        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4],
            'col2': [1, 2, 3, 4],
            'col3': [np.nan, np.nan, np.nan, 4]  # 75% missing
        })
        
        filtered_df, dropped = filter_missingness(df, threshold=0.5)
        
        assert 'col3' in dropped
        assert 'col1' not in dropped
        assert 'col2' not in dropped
        assert len(filtered_df.columns) == 2

    def test_no_columns_dropped(self):
        """Test when no columns exceed threshold."""
        df = pd.DataFrame({
            'col1': [1, 2, 3, 4],
            'col2': [1, 2, np.nan, 4]  # 25% missing
        })
        
        filtered_df, dropped = filter_missingness(df, threshold=0.5)
        
        assert len(dropped) == 0
        assert len(filtered_df.columns) == 2

class TestGenotypeEncoding:
    def test_encode_string_genotypes(self):
        """Test encoding of string genotypes."""
        df = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'chr1_SNP1': ['A/A', 'A/T', 'T/T']
        })
        
        encoded = encode_genotypes(df)
        
        assert encoded['chr1_SNP1'].iloc[0] == 0  # Homozygous
        assert encoded['chr1_SNP1'].iloc[1] == 1  # Heterozygous
        assert encoded['chr1_SNP1'].iloc[2] == 2  # Homozygous

    def test_encode_numeric_genotypes(self):
        """Test that numeric genotypes are preserved."""
        df = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'chr1_SNP1': [0, 1, 2]
        })
        
        encoded = encode_genotypes(df)
        
        assert list(encoded['chr1_SNP1']) == [0, 1, 2]

    def test_handle_missing_genotypes(self):
        """Test handling of missing genotype values."""
        df = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'chr1_SNP1': ['A/A', None, 'T/T']
        })
        
        encoded = encode_genotypes(df)
        
        assert pd.isna(encoded['chr1_SNP1'].iloc[1])
        assert encoded['chr1_SNP1'].iloc[0] == 0
        assert encoded['chr1_SNP1'].iloc[2] == 2

class TestIntegration:
    def test_full_preprocessing_pipeline(self):
        """Test a full preprocessing pipeline on mock data."""
        # Create mock data
        genomic = pd.DataFrame({
            'accession': ['A', 'B', 'C', 'D'],
            'chr1_SNP1': ['A/A', 'A/T', 'T/T', None],
            'chr2_SNP1': ['C/C', 'C/G', 'G/G', 'C/C']
        })
        
        phenotypic = pd.DataFrame({
            'accession': ['B', 'C', 'D', 'E'],
            'root_length': [10, 20, 30, 40],
            'root_angle': [15, 25, 35, 45]
        })
        
        # Match accessions
        matched_gen, matched_pheno, _ = match_accessions(genomic, phenotypic)
        
        # Filter missingness
        matched_gen, _ = filter_missingness(matched_gen, threshold=0.5)
        
        # Encode genotypes
        matched_gen = encode_genotypes(matched_gen)
        
        # Verify results
        assert len(matched_gen) == 3  # B, C, D
        assert 'chr1_SNP1' in matched_gen.columns
        assert 'chr2_SNP1' in matched_gen.columns
        assert matched_gen['chr1_SNP1'].iloc[0] == 1  # B: A/T -> 1
        assert matched_gen['chr1_SNP1'].iloc[1] == 2  # C: T/T -> 2
        assert matched_gen['chr1_SNP1'].iloc[2] == 2  # D: None -> 2 (after filtering)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])