"""
Unit tests for the logistic regression model in src/analysis/logistic_model.py.
Specifically tests handling of edge cases like zero entropy.
"""
import pytest
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Add the code directory to the path to allow imports
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.analysis.logistic_model import (
    GLMMAnalysisResult,
    load_entropy_profiles_for_analysis,
    calculate_auc_roc,
    fit_mixed_effects_model,
    stratified_analysis,
    analyze_entropy_validity_relationship
)


class TestLogisticModelZeroEntropy:
    """Tests for handling zero entropy values in logistic regression."""

    def test_handles_zero_entropy(self):
        """
        Verify that the logistic regression model does not crash when input 
        entropy values are near zero (high confidence error case).
        
        This tests the robustness of the model against edge cases where
        entropy is exactly 0 or very close to 0, which can occur when
        the model is highly confident in its predictions.
        """
        # Create a synthetic dataset with zero entropy values
        # This simulates the high confidence error case
        data = {
            'entropy': [0.0, 0.0, 0.0, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0],
            'validity': [0, 0, 0, 0, 0, 1, 1, 1, 1],  # Binary validity labels
            'sequence_id': [1, 1, 1, 2, 2, 3, 3, 4, 4],
            'task_type': ['gsm8k'] * 9
        }
        
        df = pd.DataFrame(data)
        
        # This should not raise an exception even with zero entropy values
        # The model should handle this gracefully
        result = fit_mixed_effects_model(df, 'entropy', 'validity', 'sequence_id')
        
        # Verify the result is a valid GLMMAnalysisResult object
        assert isinstance(result, GLMMAnalysisResult)
        
        # Verify that the result contains expected fields
        assert hasattr(result, 'coefficients')
        assert hasattr(result, 'p_values')
        assert hasattr(result, 'auc_roc')
        assert hasattr(result, 'significant')
        
        # The model should return a result even if the fit is not perfect
        # We just want to ensure it doesn't crash
        assert result.coefficients is not None
        assert result.p_values is not None
        assert result.auc_roc is not None
        assert isinstance(result.significant, bool)

    def test_handles_extremely_small_entropy(self):
        """
        Verify that the model handles extremely small (near-zero) entropy values.
        """
        # Create data with very small entropy values (near machine epsilon)
        data = {
            'entropy': [1e-10, 1e-10, 1e-10, 1e-8, 1e-6, 1e-3, 0.1, 0.5, 1.0],
            'validity': [0, 0, 0, 0, 0, 1, 1, 1, 1],
            'sequence_id': [1, 1, 1, 2, 2, 3, 3, 4, 4],
            'task_type': ['minigrid'] * 9
        }
        
        df = pd.DataFrame(data)
        
        # Should not raise an exception
        result = fit_mixed_effects_model(df, 'entropy', 'validity', 'sequence_id')
        
        # Verify result structure
        assert isinstance(result, GLMMAnalysisResult)
        assert result.coefficients is not None
        assert result.p_values is not None
        assert result.auc_roc is not None

    def test_zero_entropy_with_perfect_separation(self):
        """
        Test case where zero entropy leads to perfect separation.
        The model should handle this without crashing (though it may warn).
        """
        # Perfect separation case: all zero entropy -> invalid, all non-zero -> valid
        data = {
            'entropy': [0.0, 0.0, 0.0, 0.5, 0.6, 0.7],
            'validity': [0, 0, 0, 1, 1, 1],
            'sequence_id': [1, 1, 1, 2, 2, 2],
            'task_type': ['gsm8k'] * 6
        }
        
        df = pd.DataFrame(data)
        
        # Should not crash, even with perfect separation
        result = fit_mixed_effects_model(df, 'entropy', 'validity', 'sequence_id')
        
        # Verify we get a result object
        assert isinstance(result, GLMMAnalysisResult)
        assert result.coefficients is not None
        assert result.p_values is not None