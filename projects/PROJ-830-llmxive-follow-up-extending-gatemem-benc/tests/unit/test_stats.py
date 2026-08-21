"""
Unit tests for statistical analysis functions in code/utils/stats.py.
"""
import pytest
import numpy as np
from code.utils.stats import domain_stratified_analysis

def test_domain_stratified_analysis_returns_dict():
    """
    Test that domain_stratified_analysis returns a dictionary with the expected keys.
    """
    # Create mock data with two domains
    mock_data = [
        {"score": 0.8, "domain": "medical", "method": "gatekeeper", "episode_id": "e1"},
        {"score": 0.6, "domain": "medical", "method": "baseline", "episode_id": "e1"},
        {"score": 0.9, "domain": "medical", "method": "gatekeeper", "episode_id": "e2"},
        {"score": 0.7, "domain": "medical", "method": "baseline", "episode_id": "e2"},
        {"score": 0.5, "domain": "office", "method": "gatekeeper", "episode_id": "e3"},
        {"score": 0.4, "domain": "office", "method": "baseline", "episode_id": "e3"},
        {"score": 0.6, "domain": "office", "method": "gatekeeper", "episode_id": "e4"},
        {"score": 0.3, "domain": "office", "method": "baseline", "episode_id": "e4"},
    ]

    result = domain_stratified_analysis(mock_data)

    assert isinstance(result, dict), "Result must be a dictionary"
    
    expected_keys = [
        "method_used", "p_value", "test_statistic", 
        "fallback_reason", "stratified_details", "n_domains"
    ]
    
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"
    
    assert result["method_used"] == "domain_stratified_analysis"
    assert result["p_value"] is not None
    assert result["test_statistic"] is not None
    assert result["n_domains"] == 2
    assert "medical" in result["stratified_details"]
    assert "office" in result["stratified_details"]

def test_domain_stratified_analysis_insufficient_data():
    """
    Test behavior when data is insufficient for testing.
    """
    # Only one method in a domain
    mock_data = [
        {"score": 0.8, "domain": "medical", "method": "gatekeeper", "episode_id": "e1"},
        {"score": 0.6, "domain": "medical", "method": "gatekeeper", "episode_id": "e2"},
    ]

    result = domain_stratified_analysis(mock_data)

    assert isinstance(result, dict)
    assert result["method_used"] == "domain_stratified_analysis"
    assert result["p_value"] is None
    assert result["test_statistic"] is None
    assert result["fallback_reason"] == "insufficient_data"
    assert result["n_domains"] == 0

def test_domain_stratified_analysis_empty_input():
    """
    Test behavior with empty input.
    """
    with pytest.raises(ValueError, match="Input data list is empty."):
        domain_stratified_analysis([])

def test_domain_stratified_analysis_missing_keys():
    """
    Test behavior when required keys are missing in data.
    """
    mock_data = [
        {"score": 0.8, "domain": "medical"}, # Missing method
    ]

    with pytest.raises(ValueError, match="missing required keys"):
        domain_stratified_analysis(mock_data)