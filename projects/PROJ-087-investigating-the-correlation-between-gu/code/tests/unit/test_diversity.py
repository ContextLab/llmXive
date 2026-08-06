import pytest
import pandas as pd
import numpy as np
from src.diversity import rarefy_table, calculate_alpha_diversity

@pytest.fixture
def sample_otu_table():
    """Create a simple OTU table for testing."""
    data = {
        'otu_1': [100, 50, 0, 200],
        'otu_2': [50, 25, 0, 100],
        'otu_3': [25, 12, 0, 50],
        'otu_4': [10, 5, 0, 20]
    }
    index = ['sample_1', 'sample_2', 'sample_3', 'sample_4']
    return pd.DataFrame(data, index=index)

def test_rarefy_table_basic(sample_otu_table):
    """Test basic rarefaction functionality."""
    depth = 100
    rarefied = rarefy_table(sample_otu_table, depth)
    
    assert rarefied.shape == sample_otu_table.shape
    assert rarefied.index.equals(sample_otu_table.index)
    assert rarefied.columns.equals(sample_otu_table.columns)
    
    # Check that total counts are approximately equal to depth (allowing for rounding)
    for idx in rarefied.index:
        total = rarefied.loc[idx].sum()
        if sample_otu_table.loc[idx].sum() >= depth:
            assert abs(total - depth) <= depth * 0.01  # Within 1% tolerance

def test_rarefy_table_excludes_low_depth_samples(sample_otu_table):
    """Test that samples with total count < depth are excluded (set to 0)."""
    depth = 1000  # Higher than any sample
    rarefied = rarefy_table(sample_otu_table, depth)
    
    # sample_3 has total count 0, should be all zeros
    assert rarefied.loc['sample_3'].sum() == 0

def test_rarefy_table_invalid_depth(sample_otu_table):
    """Test that negative depth raises an error."""
    with pytest.raises(ValueError):
        rarefy_table(sample_otu_table, -1)

def test_rarefy_table_all_samples_excluded(sample_otu_table):
    """Test behavior when all samples are below rarefaction depth."""
    depth = 1000000
    rarefied = rarefy_table(sample_otu_table, depth)
    
    # All samples should be zeros
    assert rarefied.sum().sum() == 0

def test_rarefy_table_numpy_input(sample_otu_table):
    """Test that numpy array input is handled correctly."""
    depth = 100
    numpy_input = sample_otu_table.values
    rarefied = rarefy_table(numpy_input, depth)
    
    assert isinstance(rarefied, pd.DataFrame)
    assert rarefied.shape == sample_otu_table.shape

def test_calculate_alpha_diversity_basic(sample_otu_table):
    """Test basic alpha diversity calculation."""
    diversity = calculate_alpha_diversity(sample_otu_table, depth=100)
    
    assert diversity.shape[0] == sample_otu_table.shape[0]
    assert 'shannon' in diversity.columns
    assert 'simpson' in diversity.columns
    assert 'observed_otus' in diversity.columns
    
    # Shannon and Simpson should be non-negative
    assert (diversity['shannon'] >= 0).all()
    assert (diversity['simpson'] >= 0).all()
    assert (diversity['observed_otus'] >= 0).all()

def test_calculate_alpha_diversity_without_rarefaction(sample_otu_table):
    """Test alpha diversity calculation with pre-rarefied table."""
    rarefied = rarefy_table(sample_otu_table, 100)
    diversity = calculate_alpha_diversity(sample_otu_table, rarefied_table=rarefied)
    
    assert diversity.shape[0] == sample_otu_table.shape[0]
    assert 'shannon' in diversity.columns

def test_calculate_alpha_diversity_empty_row(sample_otu_table):
    """Test handling of samples with zero counts."""
    diversity = calculate_alpha_diversity(sample_otu_table, depth=100)
    
    # sample_3 has zero counts, should have 0 for all metrics
    assert diversity.loc['sample_3', 'shannon'] == 0.0
    assert diversity.loc['sample_3', 'simpson'] == 0.0
    assert diversity.loc['sample_3', 'observed_otus'] == 0
