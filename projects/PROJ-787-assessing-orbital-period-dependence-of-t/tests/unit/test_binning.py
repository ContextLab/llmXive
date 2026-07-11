"""
Unit tests for the binning logic (T021).
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.binning import bin_planets_by_period, create_log_bins, assign_bin_index


def test_create_log_bins():
    """Test that log-spaced bins are created correctly."""
    bins = create_log_bins(1.0, 100.0, 2)
    assert len(bins) == 2
    # Check log spacing
    log_edges = [np.log10(b[0]) for b in bins] + [np.log10(bins[-1][1])]
    diffs = np.diff(log_edges)
    assert np.allclose(diffs, diffs[0]), "Bins should be log-spaced"
    assert bins[0][0] == 1.0
    assert bins[-1][1] == 100.0


def test_assign_bin_index():
    """Test bin assignment logic."""
    bins = [(0.5, 1.0), (1.0, 2.0), (2.0, 4.0)]
    assert assign_bin_index(0.7, bins) == 0
    assert assign_bin_index(1.5, bins) == 1
    assert assign_bin_index(3.0, bins) == 2
    assert assign_bin_index(4.0, bins) == 2 # Inclusive right edge of last
    assert assign_bin_index(0.4, bins) == -1
    assert assign_bin_index(5.0, bins) == -1


def test_binning_min_size_merge():
    """Test that bins with < min_size are merged."""
    # Create a synthetic dataset with many planets in one bin and few in another
    # We need to control the binning to ensure a small bin is created.
    # Let's create a dataset that forces a specific distribution.
    
    # We will mock the data such that one log-bin has < 30 planets.
    # Since create_log_bins is deterministic, we can predict where the bins fall.
    # Let's use a small range to make bins narrow.
    
    # Generate data: 100 planets at period=10, 10 planets at period=20.
    # With default 20 bins from 0.5 to 100, the bins are wide.
    # Let's force a scenario where we have a "small" bin.
    
    # Simpler approach: Create a dataframe with specific periods that fall into specific bins
    # and ensure one bin has < 30 items.
    
    periods = []
    # Fill bin 0 (approx 0.5-1.5) with 100 planets
    periods.extend([1.0] * 100)
    # Fill bin 1 (approx 1.5-4.5) with 5 planets (underfilled)
    periods.extend([2.0] * 5)
    # Fill bin 2 (approx 4.5-13) with 100 planets
    periods.extend([10.0] * 100)
    
    df = pd.DataFrame({
        'period': periods,
        'radius': [1.0] * len(periods)
    })
    
    # Run binning with min_size=30
    result = bin_planets_by_period(df, min_period=0.5, max_period=100.0, initial_n_bins=10, min_bin_size=30)
    
    # Check that we have fewer bins than initial (merging happened)
    unique_bins = result['bin_id'].unique()
    unique_bins = [b for b in unique_bins if b != -1]
    
    # The bin with 5 planets should have been merged with a neighbor.
    # So we expect the max count per bin to be >= 30.
    counts = result['bin_id'].value_counts()
    # Check that no bin (except -1) has count < 30
    for count in counts:
        if count < 30:
            # It's possible if the merge logic failed or if the bin was merged into a neighbor
            # but the neighbor also ended up small?
            # The logic ensures we merge until no bin is < 30.
            # So this assertion should hold.
            pass # Debug if needed
    
    # Assert that all valid bins have >= 30 planets
    valid_counts = counts[counts.index != -1]
    assert all(c >= 30 for c in valid_counts), "All valid bins must have >= 30 planets"
