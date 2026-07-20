import pytest
import pandas as pd
import numpy as np
from src.diversity import rarefy_table, calculate_alpha_diversity

@pytest.fixture
def sample_otu_table():
    """Create a sample OTU table for testing."""
    data = {
        'OTU1': [100, 50, 200, 10],
        'OTU2': [50, 25, 100, 5],
        'OTU3': [25, 12, 50, 2],
        'OTU4': [10, 5, 20, 1],
        'OTU5': [5, 2, 10, 0]
    }
    index = ['Sample1', 'Sample2', 'Sample3', 'Sample4']
    return pd.DataFrame(data, index=index)

def test_rarefy_table_basic(sample_otu_table):
    """Test basic rarefaction functionality."""
    depth = 100
    rarefied = rarefy_table(sample_otu_table, depth)
    
    # Check that all samples have exactly 100 reads
    totals = rarefied.sum(axis=1)
    assert all(totals == depth), f"Expected all samples to have {depth} reads, got {totals}"
    
    # Check that shape is preserved (excluding samples that might be dropped)
    assert rarefied.shape[1] == sample_otu_table.shape[1]
    assert set(rarefied.columns) == set(sample_otu_table.columns)

def test_rarefy_table_excludes_low_depth_samples():
    """Test that samples with insufficient depth are excluded."""
    data = {
        'OTU1': [100, 10, 200],
        'OTU2': [50, 5, 100],
    }
    df = pd.DataFrame(data, index=['Sample1', 'Sample2', 'Sample3'])
    
    # Sample2 has only 15 reads, should be excluded at depth 50
    rarefied = rarefy_table(df, depth=50)
    
    assert 'Sample2' not in rarefied.index
    assert 'Sample1' in rarefied.index
    assert 'Sample3' in rarefied.index

def test_rarefy_table_invalid_depth(sample_otu_table):
    """Test that invalid depth raises error."""
    with pytest.raises(ValueError, match="positive"):
        rarefy_table(sample_otu_table, depth=0)
    
    with pytest.raises(ValueError, match="positive"):
        rarefy_table(sample_otu_table, depth=-10)

def test_rarefy_table_all_samples_excluded():
    """Test error when all samples have insufficient depth."""
    data = {
        'OTU1': [10, 5],
        'OTU2': [5, 2],
    }
    df = pd.DataFrame(data, index=['Sample1', 'Sample2'])
    
    with pytest.raises(ValueError, match="No samples have at least"):
        rarefy_table(df, depth=100)

def test_rarefy_table_numpy_input():
    """Test rarefaction with numpy array input."""
    data = np.array([
        [100, 50, 25],
        [200, 100, 50]
    ])
    rarefied = rarefy_table(data, depth=100)
    
    assert isinstance(rarefied, pd.DataFrame)
    assert all(rarefied.sum(axis=1) == 100)

def test_calculate_alpha_diversity_basic(sample_otu_table):
    """Test basic alpha diversity calculation."""
    diversity = calculate_alpha_diversity(sample_otu_table, rarefaction_depth=100)
    
    assert 'shannon' in diversity.columns
    assert 'simpson' in diversity.columns
    assert 'observed_otus' in diversity.columns
    
    # Shannon should be positive for diverse samples
    assert (diversity['shannon'] > 0).all()
    
    # Simpson should be between 0 and 1
    assert (diversity['simpson'] >= 0).all()
    assert (diversity['simpson'] <= 1).all()

def test_calculate_alpha_diversity_without_rarefaction(sample_otu_table):
    """Test alpha diversity without rarefaction."""
    diversity = calculate_alpha_diversity(sample_otu_table, rarefaction_depth=None)
    
    assert 'shannon' in diversity.columns
    assert 'simpson' in diversity.columns
    assert 'observed_otus' in diversity.columns

def test_calculate_alpha_diversity_empty_row():
    """Test handling of empty sample."""
    data = {
        'OTU1': [100, 0],
        'OTU2': [50, 0],
    }
    df = pd.DataFrame(data, index=['Sample1', 'Sample2'])
    
    diversity = calculate_alpha_diversity(df, rarefaction_depth=None)
    
    # Sample2 should have 0 diversity
    assert diversity.loc['Sample2', 'observed_otus'] == 0
    assert diversity.loc['Sample2', 'shannon'] == 0.0
    assert diversity.loc['Sample2', 'simpson'] == 0.0