"""
Unit tests for evaluation module.
"""
import pytest
import numpy as np
from evaluate import compute_confidence, flag_low_confidence_predictions

def test_confidence_calculation():
    """Test confidence score calculation."""
    # Mock predictions and true values
    predictions = np.array([0.9, 0.1, 0.8])
    true_values = np.array([1, 0, 1])
    
    # This is a placeholder; real implementation would calculate specific metrics
    confidence = compute_confidence(predictions, true_values)
    assert 0 <= confidence <= 1

def test_flag_low_confidence_predictions():
    """Test flagging of low confidence predictions."""
    predictions = [
        {"confidence": 0.8, "prediction": "hydrolysis"},
        {"confidence": 0.4, "prediction": "oxidation"},
        {"confidence": 0.7, "prediction": "hydrolysis"}
    ]
    
    flagged = flag_low_confidence_predictions(predictions, threshold=0.6)
    
    # Only the second prediction should be flagged
    assert len(flagged) == 1
    assert flagged[0]["prediction"] == "oxidation"
    assert flagged[0]["confidence"] == 0.4
