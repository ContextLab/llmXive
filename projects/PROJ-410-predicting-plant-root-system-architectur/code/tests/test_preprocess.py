"""
Unit tests for preprocessing logic.
"""
import pytest
import pandas as pd
import numpy as np
from preprocess import encode_genotypes, match_accessions, filter_missingness

class TestPreprocess:
    """Tests for preprocessing functions."""

    def test_encode_genotypes_basic(self):
        """Test basic genotype encoding (0, 1, 2)."""
        data = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'SNP1': ['0/0', '0/1', '1/1'],
            'SNP2': ['0/0', '1/1', '0/1']
        })
        
        encoded = encode_genotypes(data, ['SNP1', 'SNP2'])
        
        assert list(encoded['SNP1']) == [0, 1, 2]
        assert list(encoded['SNP2']) == [0, 2, 1]

    def test_encode_genotypes_missing(self):
        """Test handling of missing genotypes."""
        data = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'SNP1': ['0/0', './.', '1/1']
        })
        
        encoded = encode_genotypes(data, ['SNP1'])
        
        assert encoded['SNP1'].iloc[0] == 0
        assert pd.isna(encoded['SNP1'].iloc[1])
        assert encoded['SNP1'].iloc[2] == 2

    def test_match_accessions_success(self):
        """Test successful matching of accessions."""
        phenotypes = pd.DataFrame({
            'accession': ['Col-0', 'Ler-0', 'Ws-0'],
            'trait': [10, 20, 30]
        })
        
        genotypes = pd.DataFrame({
            'accession': ['Col-0', 'Ler-0', 'Ws-0', 'Sh-0'],
            'SNP1': [0, 1, 2, 0]
        })
        
        matched_pheno, matchedgeno = match_accessions(phenotypes, genotypes)
        
        assert len(matched_pheno) == 3
        assert len(matchedgeno) == 3
        assert set(matched_pheno['accession']) == {'Col-0', 'Ler-0', 'Ws-0'}

    def test_match_accessions_partial(self):
        """Test matching when some accessions are missing."""
        phenotypes = pd.DataFrame({
            'accession': ['Col-0', 'Ler-0', 'Missing'],
            'trait': [10, 20, 30]
        })
        
        genotypes = pd.DataFrame({
            'accession': ['Col-0', 'Ler-0'],
            'SNP1': [0, 1]
        })
        
        matched_pheno, matchedgeno = match_accessions(phenotypes, genotypes)
        
        assert len(matched_pheno) == 2
        assert len(matchedgeno) == 2
        assert 'Missing' not in matched_pheno['accession'].values

    def test_filter_missingness_threshold(self):
        """Test filtering columns with missingness above threshold."""
        data = pd.DataFrame({
            'accession': ['A', 'B', 'C', 'D'],
            'good': [1, 2, 3, 4],
            'bad': [1, np.nan, np.nan, np.nan],  # 75% missing
            'ok': [1, 2, np.nan, 4]  # 25% missing
        })
        
        filtered = filter_missingness(data, threshold=0.5)
        
        assert 'good' in filtered.columns
        assert 'ok' in filtered.columns
        assert 'bad' not in filtered.columns

    def test_filter_missingness_all_good(self):
        """Test when no columns exceed threshold."""
        data = pd.DataFrame({
            'accession': ['A', 'B', 'C'],
            'SNP1': [1, 2, 3],
            'SNP2': [4, 5, 6]
        })
        
        filtered = filter_missingness(data, threshold=0.1)
        
        assert set(filtered.columns) == {'accession', 'SNP1', 'SNP2'}
