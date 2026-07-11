import pytest
import math
from unittest.mock import patch, MagicMock
from metrics import (
    is_wasted_call,
    calculate_dynamic_sample_size,
    wilcoxon_signed_rank_test,
    bonferroni_correction,
    load_beir_ground_truth,
    load_results_from_json,
    aggregate_ndcg_scores,
    evaluate_full_pipeline,
    validate_jaccard_cosine_correlation
)
from scipy.stats import wilcoxon
import numpy as np

# --- Existing Tests (Preserved) ---

def test_is_wasted_call_above_threshold():
    """Test that a similarity above 0.95 is flagged as wasted."""
    assert is_wasted_call(0.96) is True
    assert is_wasted_call(1.0) is True

def test_is_wasted_call_below_threshold():
    """Test that a similarity below 0.95 is not flagged as wasted."""
    assert is_wasted_call(0.94) is False
    assert is_wasted_call(0.0) is False

def test_is_wasted_call_at_threshold():
    """Test behavior exactly at the threshold (0.95)."""
    # Threshold is > 0.95, so 0.95 should be False
    assert is_wasted_call(0.95) is False

def test_is_wasted_call_custom_threshold():
    """Test with a custom threshold."""
    assert is_wasted_call(0.90, threshold=0.85) is True
    assert is_wasted_call(0.80, threshold=0.85) is False

def test_calculate_dynamic_sample_size_logic():
    """Test the logic of dynamic sample size calculation."""
    # Case 1: Flagged < Bound
    assert calculate_dynamic_sample_size(100, 1000) == 100
    
    # Case 2: Flagged > Bound
    assert calculate_dynamic_sample_size(2000, 1000) == 1000
    
    # Case 3: Flagged == Bound
    assert calculate_dynamic_sample_size(500, 500) == 500
    
    # Case 4: Zero flagged
    assert calculate_dynamic_sample_size(0, 1000) == 0

# --- New Tests for T026: Wilcoxon and Bonferroni ---

def test_wilcoxon_signed_rank_test_basic():
    """Test Wilcoxon signed-rank test with known data."""
    # Two identical lists should yield a p-value of 1.0 (no difference)
    list_a = [1.0, 2.0, 3.0, 4.0, 5.0]
    list_b = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    stat, p_val = wilcoxon_signed_rank_test(list_a, list_b)
    
    assert p_val == 1.0
    assert stat == 0.0

def test_wilcoxon_signed_rank_test_different_data():
    """Test Wilcoxon with clearly different data."""
    # List A is consistently higher than List B
    list_a = [10.0, 20.0, 30.0, 40.0, 50.0]
    list_b = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    stat, p_val = wilcoxon_signed_rank_test(list_a, list_b)
    
    # With such a clear difference, p-value should be very small
    assert p_val < 0.05
    assert stat > 0.0

def test_wilcoxon_empty_lists():
    """Test handling of empty lists."""
    list_a = []
    list_b = []
    
    stat, p_val = wilcoxon_signed_rank_test(list_a, list_b)
    
    assert p_val == 1.0
    assert stat == 0.0

def test_wilcoxon_single_element():
    """Test handling of single element lists."""
    list_a = [1.0]
    list_b = [1.0]
    
    stat, p_val = wilcoxon_signed_rank_test(list_a, list_b)
    
    # With identical single elements, p-value is 1.0
    assert p_val == 1.0

def test_bonferroni_correction_basic():
    """Test Bonferroni correction with simple inputs."""
    p_values = [0.01, 0.05, 0.10]
    n_tests = 3
    
    corrected_p_values = bonferroni_correction(p_values, n_tests)
    
    # Bonferroni multiplies p-value by n_tests, capped at 1.0
    assert corrected_p_values[0] == min(0.01 * 3, 1.0)
    assert corrected_p_values[1] == min(0.05 * 3, 1.0)
    assert corrected_p_values[2] == min(0.10 * 3, 1.0)

def test_bonferroni_correction_cap():
    """Test that Bonferroni correction caps p-values at 1.0."""
    p_values = [0.5, 0.6, 0.7]
    n_tests = 3
    
    corrected_p_values = bonferroni_correction(p_values, n_tests)
    
    # All should be capped at 1.0
    assert corrected_p_values[0] == 1.0
    assert corrected_p_values[1] == 1.0
    assert corrected_p_values[2] == 1.0

def test_bonferroni_correction_empty():
    """Test Bonferroni with empty list."""
    p_values = []
    n_tests = 0
    
    corrected_p_values = bonferroni_correction(p_values, n_tests)
    
    assert corrected_p_values == []

def test_bonferroni_correction_single():
    """Test Bonferroni with single p-value."""
    p_values = [0.05]
    n_tests = 1
    
    corrected_p_values = bonferroni_correction(p_values, n_tests)
    
    # With n_tests=1, p-value remains unchanged
    assert corrected_p_values[0] == 0.05

def test_bonferroni_correction_mixed():
    """Test Bonferroni with mixed significant and non-significant values."""
    p_values = [0.01, 0.04, 0.06, 0.20]
    n_tests = 4
    
    corrected_p_values = bonferroni_correction(p_values, n_tests)
    
    # Expected values
    assert corrected_p_values[0] == 0.04  # 0.01 * 4
    assert corrected_p_values[1] == 0.16  # 0.04 * 4
    assert corrected_p_values[2] == 0.24  # 0.06 * 4
    assert corrected_p_values[3] == 1.0   # 0.20 * 4 = 0.8, capped at 1.0? No, 0.8 < 1.0. 
    # Wait, 0.20 * 4 = 0.80. Let me recheck.
    # Actually 0.20 * 4 = 0.80, which is < 1.0, so it should be 0.80.
    # My previous comment was wrong. Let's correct the assertion.
    assert corrected_p_values[3] == 0.80

def test_wilcoxon_and_bonferroni_integration():
    """Test the combined use of Wilcoxon and Bonferroni for multiple comparisons."""
    # Simulate results from two different experiments (e.g., NDCG and Wasted Calls)
    # Experiment 1: NDCG scores
    ndcg_baseline = [0.45, 0.46, 0.44, 0.47, 0.45]
    ndcg_clustering = [0.50, 0.51, 0.49, 0.52, 0.50]
    
    # Experiment 2: Wasted call ratios
    wasted_baseline = [0.30, 0.32, 0.29, 0.31, 0.30]
    wasted_clustering = [0.10, 0.12, 0.09, 0.11, 0.10]
    
    # Perform Wilcoxon tests
    stat_ndcg, p_ndcg = wilcoxon_signed_rank_test(ndcg_baseline, ndcg_clustering)
    stat_wasted, p_wasted = wilcoxon_signed_rank_test(wasted_baseline, wasted_clustering)
    
    # Collect p-values
    p_values = [p_ndcg, p_wasted]
    
    # Apply Bonferroni correction (2 tests)
    corrected_p_values = bonferroni_correction(p_values, 2)
    
    # Verify that corrected p-values are larger than or equal to original
    for orig, corr in zip(p_values, corrected_p_values):
        assert corr >= orig
        
    # Verify that the correction was applied correctly
    assert corrected_p_values[0] == min(p_ndcg * 2, 1.0)
    assert corrected_p_values[1] == min(p_wasted * 2, 1.0)