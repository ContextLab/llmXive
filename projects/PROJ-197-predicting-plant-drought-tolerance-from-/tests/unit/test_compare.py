"""
Unit tests for the comparison module.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module
from models.compare import perform_rf_vs_xgb_ttest, classify_features

def test_perform_rf_vs_xgb_ttest():
    """Test paired t-test function."""
    # Generate synthetic scores
    np.random.seed(42)
    rf_scores = np.random.uniform(0.7, 0.9, 10)
    xgb_scores = np.random.uniform(0.7, 0.9, 10)
    
    result = perform_rf_vs_xgb_ttest(rf_scores.tolist(), xgb_scores.tolist())
    
    assert "t_statistic" in result
    assert "p_value" in result
    assert "significant_at_0.05" in result
    assert "winner" in result

def test_classify_features():
    """Test feature classification."""
    df = pd.DataFrame({
        "feature": ["gene1", "trait1", "gene2"],
        "importance": [0.5, 0.3, 0.2]
    })
    
    genomic = ["gene1", "gene2"]
    physio = ["trait1"]
    
    classified = classify_features(df, genomic, physio)
    
    assert classified.loc[0, "category"] == "Genomic"
    assert classified.loc[1, "category"] == "Physiological"
    assert classified.loc[2, "category"] == "Genomic"