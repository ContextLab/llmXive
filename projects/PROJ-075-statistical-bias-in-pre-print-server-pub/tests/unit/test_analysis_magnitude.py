import pytest
import numpy as np
from scipy import stats
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

def test_paired_ttest_logic():
    """Test paired t-test logic for effect size differences."""
    # Simulate paired effect sizes
    preprint_es = np.array([0.5, 0.6, 0.4, 0.7, 0.5])
    journal_es = np.array([0.6, 0.7, 0.5, 0.8, 0.6])
    
    # Calculate differences
    diffs = journal_es - preprint_es
    
    # Perform t-test
    t_stat, p_val = stats.ttest_rel(preprint_es, journal_es)
    
    # Verify the test runs and returns valid stats
    assert not np.isnan(t_stat)
    assert 0 <= p_val <= 1

def test_wilcoxon_logic():
    """Test Wilcoxon signed-rank test logic."""
    preprint_es = np.array([0.5, 0.6, 0.4, 0.7, 0.5])
    journal_es = np.array([0.6, 0.7, 0.5, 0.8, 0.6])
    
    # Perform Wilcoxon test
    stat, p_val = stats.wilcoxon(preprint_es, journal_es)
    
    assert not np.isnan(stat)
    assert 0 <= p_val <= 1
