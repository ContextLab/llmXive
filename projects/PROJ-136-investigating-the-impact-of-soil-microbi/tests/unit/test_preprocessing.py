"""
Unit tests for preprocessing module (T017).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

# Import the function to test
from code.analysis.preprocessing import filter_taxon_by_presence, run_taxon_filtering

@pytest.fixture
def sample_otu_table():
    """
    Create a small synthetic OTU table for testing.
    Rows: Samples, Cols: Taxa
    """
    data = {
        'Taxon_A': [10, 5, 0, 0, 0],   # Present in 2/5 (40%) -> Keep
        'Taxon_B': [0, 0, 0, 0, 0],    # Present in 0/5 (0%) -> Drop
        'Taxon_C': [1, 2, 3, 4, 5],    # Present in 5/5 (100%) -> Keep
        'Taxon_D': [0, 0, 1, 0, 0],    # Present in 1/5 (20%) -> Keep (if threshold < 20%)
        'Taxon_E': [0, 0, 0, 0, 1],    # Present in 1/5 (20%) -> Keep (if threshold < 20%)
    }
    df = pd.DataFrame(data, index=['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4', 'Sample_5'])
    return df

def test_filter_taxon_by_presence_keep_all():
    """Test with threshold 0.0 (keep everything)"""
    table = pd.DataFrame({'A': [1, 0], 'B': [0, 0]})
    result = filter_taxon_by_presence(table, min_sample_fraction=0.0)
    assert list(result.columns) == ['A', 'B']

def test_filter_taxon_by_presence_drop_rare(sample_otu_table):
    """Test with threshold 0.5 (50% of samples)"""
    # Taxon_A: 2/5 (40%) -> Drop
    # Taxon_B: 0/5 (0%) -> Drop
    # Taxon_C: 5/5 (100%) -> Keep
    # Taxon_D: 1/5 (20%) -> Drop
    # Taxon_E: 1/5 (20%) -> Drop
    result = filter_taxon_by_presence(sample_otu_table, min_sample_fraction=0.5)
    
    assert 'Taxon_C' in result.columns
    assert 'Taxon_A' not in result.columns
    assert 'Taxon_B' not in result.columns
    assert 'Taxon_D' not in result.columns
    assert 'Taxon_E' not in result.columns
    assert len(result.columns) == 1

def test_filter_taxon_by_presence_threshold_5_percent(sample_otu_table):
    """Test with default 5% threshold (1 sample)"""
    # All taxa with at least 1 count should be kept.
    # Taxon_B is all zeros -> Drop.
    result = filter_taxon_by_presence(sample_otu_table, min_sample_fraction=0.05)
    
    assert 'Taxon_B' not in result.columns
    assert 'Taxon_A' in result.columns
    assert 'Taxon_C' in result.columns
    assert 'Taxon_D' in result.columns
    assert 'Taxon_E' in result.columns

def test_filter_taxon_by_presence_empty_table():
    """Test with empty table"""
    table = pd.DataFrame()
    with pytest.raises(ValueError):
        filter_taxon_by_presence(table)

def test_run_taxon_filtering_integration():
    """Test the full pipeline with a temporary file"""
    data = {
        'Taxon_X': [10, 0, 0, 0, 0],
        'Taxon_Y': [1, 1, 1, 1, 1],
        'Taxon_Z': [0, 0, 0, 0, 0],
    }
    df = pd.DataFrame(data, index=[f'Sample_{i}' for i in range(5)])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path)
        
        stats = run_taxon_filtering(str(input_path), str(output_path), min_sample_fraction=0.2)
        
        assert stats['status'] == 'completed'
        assert stats['input_taxa'] == 3
        assert stats['output_taxa'] == 1 # Only Taxon_Y (20% threshold requires 1 sample, so Taxon_X is kept? 1/5=20%. Yes.)
        # Wait: 0.2 * 5 = 1. Taxon_X has 1 sample. Taxon_Y has 5. Taxon_Z has 0.
        # So output should have Taxon_X and Taxon_Y.
        assert stats['output_taxa'] == 2 
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content
        result_df = pd.read_csv(output_path, index_col=0)
        assert 'Taxon_X' in result_df.columns
        assert 'Taxon_Y' in result_df.columns
        assert 'Taxon_Z' not in result_df.columns