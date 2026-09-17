"""
Unit tests for statistical analysis functions in code/utils/stats.py
"""

import pytest
import numpy as np
import pandas as pd
from code.utils.stats import shapiro_wilk_test, fit_lmm, fit_fixed_effects_glm, domain_stratified_analysis, run_post_hoc, pair_episodes, run_full_stats_pipeline

def test_shapiro_wilk_returns_p_value():
    """Test that shapiro_wilk_test returns a dict with p_value."""
    # Normal data
    data = np.random.normal(0, 1, 50)
    result = shapiro_wilk_test(data)
    
    assert isinstance(result, dict)
    assert "p_value" in result
    assert "statistic" in result
    assert "is_normal" in result
    assert isinstance(result["p_value"], float)
    assert 0.0 <= result["p_value"] <= 1.0
    
def test_shapiro_wilk_empty_input():
    """Test error handling for empty input."""
    with pytest.raises(ValueError):
        shapiro_wilk_test([])
        
def test_shapiro_wilk_too_few_samples():
    """Test error handling for fewer than 3 samples."""
    with pytest.raises(ValueError):
        shapiro_wilk_test([1.0, 2.0])
        
def test_pair_episodes():
    """Test pairing logic."""
    gatekeeper = [
        {"episode_id": "1", "score": 0.9},
        {"episode_id": "2", "score": 0.8}
    ]
    baseline = [
        {"episode_id": "1", "score": 0.7},
        {"episode_id": "2", "score": 0.6}
    ]
    
    paired = pair_episodes(gatekeeper, baseline)
    
    assert len(paired) == 2
    assert paired[0]["episode_id"] == "1"
    assert paired[0]["score_gatekeeper"] == 0.9
    assert paired[0]["score_baseline"] == 0.7
    
def test_pair_episodes_missing_id():
    """Test error when episode_id is missing in baseline."""
    gatekeeper = [{"episode_id": "1", "score": 0.9}]
    baseline = [{"episode_id": "2", "score": 0.7}]
    
    with pytest.raises(ValueError):
        pair_episodes(gatekeeper, baseline)
        
def test_run_post_hoc_normal():
    """Test post-hoc selection for normal data."""
    data = np.random.normal(0, 1, 50)
    result = run_post_hoc(data, is_normal=True)
    assert result["test"] == "t-test (paired)"
    assert "p_value" in result
    
def test_run_post_hoc_non_normal():
    """Test post-hoc selection for non-normal data."""
    data = np.random.exponential(1, 50)
    result = run_post_hoc(data, is_normal=False)
    assert result["test"] == "Wilcoxon (paired)"
    assert "p_value" in result