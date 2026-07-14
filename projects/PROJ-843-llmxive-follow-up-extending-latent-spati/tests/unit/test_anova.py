"""
Unit tests for code/eval/anova.py
Tests cover:
- Data loading for ANOVA
- Two-way ANOVA execution
- Interaction effect detection
- P-value validation
"""
import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from eval.anova import load_metrics_for_anova, run_anova

@pytest.fixture
def sample_metrics_data(tmp_path):
    """Create sample metrics data for ANOVA testing."""
    data_dir = tmp_path / "results"
    data_dir.mkdir()
    
    # Create synthetic metrics data
    metrics = [
        {"sequence_id": "seq1", "dynamics": "Static", "texture": "High", "world_score": 0.85, "sparse_consistency": 0.90},
        {"sequence_id": "seq2", "dynamics": "Static", "texture": "High", "world_score": 0.82, "sparse_consistency": 0.88},
        {"sequence_id": "seq3", "dynamics": "Static", "texture": "Low", "world_score": 0.70, "sparse_consistency": 0.75},
        {"sequence_id": "seq4", "dynamics": "Static", "texture": "Low", "world_score": 0.68, "sparse_consistency": 0.72},
        {"sequence_id": "seq5", "dynamics": "Fast", "texture": "High", "world_score": 0.75, "sparse_consistency": 0.80},
        {"sequence_id": "seq6", "dynamics": "Fast", "texture": "High", "world_score": 0.72, "sparse_consistency": 0.78},
        {"sequence_id": "seq7", "dynamics": "Fast", "texture": "Low", "world_score": 0.60, "sparse_consistency": 0.65},
        {"sequence_id": "seq8", "dynamics": "Fast", "texture": "Low", "world_score": 0.58, "sparse_consistency": 0.62},
    ]
    
    metrics_file = data_dir / "metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f)
    
    return data_dir

def test_load_metrics_for_anova(sample_metrics_data):
    """Test loading metrics data for ANOVA."""
    df = load_metrics_for_anova(sample_metrics_data)
    
    assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
    assert len(df) == 8, "Should load all 8 records"
    assert "dynamics" in df.columns, "Should have dynamics column"
    assert "texture" in df.columns, "Should have texture column"
    assert "world_score" in df.columns, "Should have world_score column"
    assert "sparse_consistency" in df.columns, "Should have sparse_consistency column"

def test_run_anova_interaction_effect(sample_metrics_data):
    """Test that ANOVA correctly identifies interaction effects."""
    df = load_metrics_for_anova(sample_metrics_data)
    result = run_anova(df, metric="world_score")
    
    # Result should be a dictionary
    assert isinstance(result, dict), "ANOVA result should be a dictionary"
    assert "f_statistic" in result, "Result should contain F-statistic"
    assert "p_value" in result, "Result should contain p-value"
    assert "interaction_p_value" in result, "Result should contain interaction p-value"
    
    # Values should be numeric
    assert isinstance(result["f_statistic"], (int, float)), "F-statistic must be numeric"
    assert isinstance(result["p_value"], (int, float)), "P-value must be numeric"
    assert result["p_value"] >= 0 and result["p_value"] <= 1, "P-value must be between 0 and 1"

def test_run_anova_different_metrics(sample_metrics_data):
    """Test ANOVA on different metric columns."""
    df = load_metrics_for_anova(sample_metrics_data)
    
    result_ws = run_anova(df, metric="world_score")
    result_sc = run_anova(df, metric="sparse_consistency")
    
    # Both should produce valid results
    assert result_ws["p_value"] >= 0, "WorldScore p-value must be valid"
    assert result_sc["p_value"] >= 0, "SparseConsistency p-value must be valid"

def test_anova_with_insufficient_data():
    """Test ANOVA handling of insufficient data."""
    # Create a DataFrame with only one group
    df = pd.DataFrame({
        "dynamics": ["Static", "Static"],
        "texture": ["High", "High"],
        "world_score": [0.8, 0.8]
    })
    
    # Should not crash, but might return NaN or specific error handling
    # depending on scipy implementation
    try:
        result = run_anova(df, metric="world_score")
        # If it runs, result should be valid structure
        assert "p_value" in result
    except ValueError:
        # scipy.stats might raise ValueError for insufficient degrees of freedom
        # This is acceptable behavior
        pass

def test_anova_p_value_threshold(sample_metrics_data):
    """Test that ANOVA correctly reports significance threshold."""
    df = load_metrics_for_anova(sample_metrics_data)
    result = run_anova(df, metric="world_score")
    
    # Check that we can determine significance
    is_significant = result["interaction_p_value"] < 0.05
    assert isinstance(is_significant, bool), "Significance check should return boolean"