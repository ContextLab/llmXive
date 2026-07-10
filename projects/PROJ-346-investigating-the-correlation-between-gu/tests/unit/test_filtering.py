import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure code directory is in path for imports
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import filter_low_read_samples, filter_rare_taxa, get_logger

@pytest.fixture
def sample_microbiome_data():
    """
    Create a sample DataFrame mimicking microbiome abundance data.
    Columns: 'sample_id', 'read_count', 'taxon', 'abundance'
    """
    data = {
        'sample_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S3', 'S3', 'S3'],
        'read_count': [15000, 15000, 15000, 5000, 5000, 5000, 20000, 20000, 20000],
        'taxon': ['Bacteroides', 'Firmicutes', 'Actinobacteria',
                  'Bacteroides', 'Firmicutes', 'Actinobacteria',
                  'Bacteroides', 'Firmicutes', 'Actinobacteria'],
        'abundance': [0.5, 0.4, 0.1,
                      0.6, 0.3, 0.1,
                      0.2, 0.7, 0.1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_taxa_counts():
    """
    Create a sample DataFrame mimicking aggregated taxa counts per sample.
    Columns: 'sample_id', 'Bacteroides', 'Firmicutes', 'Actinobacteria', 'RareTaxon'
    """
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'Bacteroides': [1000, 500, 2000, 100],
        'Firmicutes': [800, 300, 1400, 50],
        'Actinobacteria': [200, 100, 400, 10],
        'RareTaxon': [1, 0, 2, 0]  # Very rare taxa to test filtering
    }
    return pd.DataFrame(data)

def test_remove_low_read_samples(sample_microbiome_data):
    """
    Test that samples with read_count < 10,000 are removed.
    Expected: S2 (5000 reads) removed. S1 and S3 kept.
    """
    # Threshold is typically 10,000 based on project specs (FR-001)
    threshold = 10000
    
    # Call the function
    filtered_df = filter_low_read_samples(sample_microbiome_data, threshold)
    
    # Assertions
    assert 'S2' not in filtered_df['sample_id'].unique(), \
        "Sample S2 with 5000 reads should be removed"
    assert set(filtered_df['sample_id'].unique()) == {'S1', 'S3'}, \
        "Only S1 and S3 should remain"
    assert len(filtered_df) == 6, \
        "Expected 6 rows (3 taxa * 2 samples)"

def test_remove_rare_taxa(sample_taxa_counts):
    """
    Test that taxa with abundance < 0.1% (0.001) across all samples are removed.
    Note: The function logic usually filters based on a minimum occurrence or average abundance.
    Assuming standard behavior: remove columns where sum(abundance) < threshold or similar.
    Here we test based on the 'RareTaxon' column having very low counts.
    
    We will simulate the abundance calculation if the function expects raw counts or relative abundance.
    Based on typical microbiome preprocessing:
    1. Calculate relative abundance per sample.
    2. Filter taxa that are < 0.001 in all samples or average < 0.001.
    
    Let's assume the function filters taxa that do not meet a minimum relative abundance threshold
    across the dataset.
    """
    # Threshold for abundance is 0.001 (0.1%)
    abundance_threshold = 0.001
    
    # Calculate total reads per sample to simulate relative abundance context
    # The function filter_rare_taxa likely handles the conversion or expects pre-normalized data.
    # If it expects counts, it might calculate relative abundance internally.
    # Let's assume it takes the raw counts dataframe and a threshold.
    
    # In the sample data, 'RareTaxon' has very low counts compared to others.
    # Total reads per sample:
    # S1: 1801, S2: 800, S3: 3402, S4: 160
    # Relative abundance of RareTaxon:
    # S1: 1/1801 ~ 0.00055 (< 0.001)
    # S2: 0
    # S3: 2/3402 ~ 0.00058 (< 0.001)
    # S4: 0
    # It should be removed.
    
    filtered_df = filter_rare_taxa(sample_taxa_counts, abundance_threshold)
    
    # Assertions
    assert 'RareTaxon' not in filtered_df.columns, \
        "RareTaxon should be removed due to low abundance"
    assert set(filtered_df.columns) == {'sample_id', 'Bacteroides', 'Firmicutes', 'Actinobacteria'}, \
        "Only common taxa should remain"
    assert len(filtered_df) == 4, \
        "Sample rows should be preserved, only columns (taxa) removed"

def test_filter_low_read_samples_empty_input():
    """Test handling of empty DataFrame"""
    df = pd.DataFrame(columns=['sample_id', 'read_count', 'taxon', 'abundance'])
    result = filter_low_read_samples(df, 10000)
    assert result.empty

def test_filter_rare_taxa_empty_input():
    """Test handling of empty DataFrame"""
    df = pd.DataFrame(columns=['sample_id', 'TaxonA'])
    result = filter_rare_taxa(df, 0.001)
    assert result.empty