import pytest
import pandas as pd
import numpy as np
from src.diversity import rarefy_table, calculate_alpha_diversity

@pytest.fixture
def sample_otu_table():
    """Create a simple OTU table for testing."""
    data = {
        'OTU_1': [100, 50, 200],
        'OTU_2': [50, 25, 100],
        'OTU_3': [50, 25, 100]
    }
    index = ['sample_1', 'sample_2', 'sample_3']
    return pd.DataFrame(data, index=index)

def test_rarefy_table_basic(sample_otu_table):
    """Test basic rarefaction functionality."""
    depth = 100
    result = rarefy_table(sample_otu_table, depth)
    
    assert result.shape[0] == 3, "All samples should be retained"
    assert result.shape[1] == 3, "All OTUs should be retained"
    assert result.sum(axis=1).eq(depth).all(), "All samples should have exactly 'depth' reads"
    assert result.min().min() >= 0, "No negative counts"

def test_rarefy_table_excludes_low_depth_samples(sample_otu_table):
    """Test that samples with insufficient depth are excluded."""
    depth = 200  # sample_2 has only 100 total reads
    result = rarefy_table(sample_otu_table, depth)
    
    assert result.shape[0] == 2, "Only samples with >= 200 reads should be retained"
    assert 'sample_2' not in result.index, "sample_2 should be excluded"
    assert result.sum(axis=1).eq(depth).all(), "Remaining samples should have exactly 'depth' reads"

def test_rarefy_table_invalid_depth(sample_otu_table):
    """Test that invalid depth raises ValueError."""
    with pytest.raises(ValueError):
        rarefy_table(sample_otu_table, 0)
    
    with pytest.raises(ValueError):
        rarefy_table(sample_otu_table, -10)

def test_rarefy_table_all_samples_excluded(sample_otu_table):
    """Test error when all samples are excluded due to depth."""
    depth = 10000  # Much higher than any sample
    with pytest.raises(ValueError):
        rarefy_table(sample_otu_table, depth)

def test_rarefy_table_numpy_input(sample_otu_table):
    """Test rarefaction with numpy array input."""
    depth = 100
    np_array = sample_otu_table.values
    result = rarefy_table(np_array, depth)
    
    assert result.shape[0] == 3
    assert result.sum(axis=1).eq(depth).all()

def test_calculate_alpha_diversity_basic(sample_otu_table):
    """Test alpha diversity calculation."""
    rarefied = rarefy_table(sample_otu_table, 100)
    alpha_metrics = calculate_alpha_diversity(rarefied)
    
    assert 'shannon' in alpha_metrics.columns
    assert 'simpson' in alpha_metrics.columns
    assert 'observed_otus' in alpha_metrics.columns
    assert alpha_metrics.shape[0] == 3

def test_calculate_alpha_diversity_without_rarefaction():
    """Test that alpha diversity can be calculated on non-rarefied data (though not recommended)."""
    data = {'OTU_1': [100, 50], 'OTU_2': [50, 25]}
    df = pd.DataFrame(data, index=['s1', 's2'])
    # This should work, though rarefaction is the standard precursor
    metrics = calculate_alpha_diversity(df)
    assert metrics.shape[0] == 2

def test_calculate_alpha_diversity_empty_row():
    """Test handling of a sample with zero reads."""
    data = {'OTU_1': [100, 0], 'OTU_2': [50, 0]}
    df = pd.DataFrame(data, index=['s1', 's2'])
    metrics = calculate_alpha_diversity(df)
    # The empty row should have 0 for all metrics or NaN depending on implementation
    # Our implementation sets 0.0 for empty sums
    assert metrics.loc['s2', 'observed_otus'] == 0
    assert metrics.loc['s2', 'shannon'] == 0.0
    assert metrics.loc['s2', 'simpson'] == 0.0
