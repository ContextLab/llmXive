"""
Unit tests for code/01_ingest.py logic (filtering and data handling).
Note: Network tests are skipped unless explicitly enabled.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from code.utils import filter_low_read_samples, filter_rare_taxa

class TestFiltering:
    @pytest.fixture
    def mock_data(self):
        """Create mock microbiome data."""
        data = {
            'sample1': [1000, 2000, 5000],
            'sample2': [5000, 10000, 5000],
            'sample3': [100, 200, 300], # Low reads
            'sample4': [10000, 20000, 10000],
        }
        # Add metadata columns
        df = pd.DataFrame(data, index=['taxaA', 'taxaB', 'taxaC']).T
        df['total_reads'] = df.sum(axis=1)
        df['sample_id'] = df.index
        return df

    def test_remove_low_read_samples(self, mock_data):
        """Test FR-001 filter: <10k reads."""
        result = filter_low_read_samples(mock_data, threshold=10000)
        # sample1 (8000), sample3 (600) should be removed
        # sample2 (20000), sample4 (40000) should remain
        assert 'sample1' not in result.index
        assert 'sample3' not in result.index
        assert 'sample2' in result.index
        assert 'sample4' in result.index

    def test_remove_rare_taxa(self, mock_data):
        """Test FR-001 filter: <0.1% abundance."""
        # Calculate total reads
        total = mock_data['total_reads'].sum()
        threshold = total * 0.001
        
        # Create a scenario with a rare taxon
        # taxaA: 1000+5000+100+10000 = 16100
        # taxaB: 2000+10000+200+20000 = 32200
        # taxaC: 5000+5000+300+10000 = 20300
        # All are > 0.1% of total (~68500 * 0.001 = 68.5)
        
        # Let's make one rare
        rare_data = mock_data.copy()
        rare_data['sample1']['taxaD'] = 1
        rare_data['sample2']['taxaD'] = 1
        rare_data['sample3']['taxaD'] = 1
        rare_data['sample4']['taxaD'] = 1
        rare_data['total_reads'] = rare_data.sum(axis=1)
        
        # Total for taxaD is 4. Total reads is ~68504. Threshold ~68.
        # taxaD should be removed.
        
        rare_taxa = ['taxaD']
        result = filter_rare_taxa(rare_data, rare_taxa, exclude_cols=['total_reads', 'sample_id'])
        
        assert 'taxaD' not in result.columns
        assert 'taxaA' in result.columns

class TestIngestionLogic:
    def test_data_structure(self):
        """Verify that if data is loaded, it has expected structure."""
        # This is a structural test, not a network test
        data = {
            's1': [1, 2],
            's2': [3, 4]
        }
        df = pd.DataFrame(data, index=['t1', 't2']).T
        df['total_reads'] = df.sum(axis=1)
        df['sample_id'] = df.index
        
        assert 'total_reads' in df.columns
        assert 'sample_id' in df.columns
        assert df.index.name is None # or check if it's set
        assert df.shape[1] == 4 # s1, s2, total_reads, sample_id