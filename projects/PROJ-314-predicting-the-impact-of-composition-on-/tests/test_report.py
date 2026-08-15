import pytest
import json
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from report import calculate_cv_stability

class TestCVStabilityLogic:
    """
    Unit tests for T058: Validate CV Calculation Logic.
    
    Ensures that calculate_cv_stability() computes the Coefficient of Variation (CV)
    on the *mean* importance of the top 5 features *across folds*, rather than on
    raw per-fold values.
    
    SC-002 Requirement: "The CV of the top 5 feature importance scores across 
    cross-validation folds must be computed correctly."
    """

    def test_cv_stability_logic_mean_across_folds(self):
        """
        Verify that CV is calculated on the MEAN of top features across folds.
        
        Scenario:
        - We have 3 folds.
        - We have 5 features.
        - We verify that the function averages the importance scores per feature 
          across the 3 folds first, then computes the CV of those 5 mean values.
        """
        # Mock data: 3 folds, 5 features
        # Fold 0: [10, 20, 30, 40, 50]
        # Fold 1: [12, 22, 32, 42, 52]
        # Fold 2: [11, 21, 31, 41, 51]
        
        # Mean of Feature 0: (10+12+11)/3 = 11.0
        # Mean of Feature 1: (20+22+21)/3 = 21.0
        # Mean of Feature 2: (30+32+31)/3 = 31.0
        # Mean of Feature 3: (40+42+41)/3 = 41.0
        # Mean of Feature 4: (50+52+51)/3 = 51.0
        
        # The means are: [11, 21, 31, 41, 51]
        # Mean of these means: (11+21+31+41+51)/5 = 31.0
        # Std Dev of these means:
        #   Var = [(11-31)^2 + (21-31)^2 + (31-31)^2 + (41-31)^2 + (51-31)^2] / (5-1)
        #       = [400 + 100 + 0 + 100 + 400] / 4 = 1000 / 4 = 250
        #   Std = sqrt(250) ≈ 15.811
        # CV = Std / Mean = 15.811 / 31.0 ≈ 0.51003
          
        per_fold_importances = [
            np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
            np.array([12.0, 22.0, 32.0, 42.0, 52.0]),
            np.array([11.0, 21.0, 31.0, 41.0, 51.0])
        ]
        
        # Expected calculation
        expected_means = np.mean(per_fold_importances, axis=0)
        expected_mean_of_means = np.mean(expected_means)
        expected_std_of_means = np.std(expected_means, ddof=1)
        expected_cv = expected_std_of_means / expected_mean_of_means
          
        # Call the function
        result = calculate_cv_stability(per_fold_importances)
        
        # Assertions
        assert 'cv_score' in result, "Result must contain 'cv_score'"
        assert 'top_5_features' in result, "Result must contain 'top_5_features'"
        assert 'mean_importances' in result, "Result must contain 'mean_importances'"
        
        # Check the CV score matches our manual calculation (within float tolerance)
        assert np.isclose(result['cv_score'], expected_cv, rtol=1e-4), \
            f"CV mismatch: got {result['cv_score']}, expected {expected_cv}"
            
        # Check that the mean importances match
        assert np.allclose(result['mean_importances'], expected_means), \
            f"Mean importances mismatch: got {result['mean_importances']}, expected {expected_means}"
            
        # Verify the logic: if we passed raw values (flattened), the CV would be different.
        # Flattened values: [10, 12, 11, 20, 22, 21, ...]
        # This test specifically ensures we are averaging ACROSS folds first.

    def test_cv_stability_with_single_fold(self):
        """
        Verify behavior when only 1 fold is provided.
        CV is undefined (division by zero in std) or 0.0 depending on implementation.
        With ddof=1, std of a single value is 0 (or NaN if N=1).
        """
        per_fold_importances = [np.array([10.0, 20.0, 30.0, 40.0, 50.0])]
        
        result = calculate_cv_stability(per_fold_importances)
        
        # With a single fold, the mean is the value itself.
        # Std dev of a single value (ddof=1) is 0.0.
        # CV = 0 / Mean = 0.0
        assert result['cv_score'] == 0.0, "CV for single fold should be 0.0"

    def test_cv_stability_with_top_5_selection(self):
        """
        Verify that only the TOP 5 features are used for CV calculation,
        even if more features are provided.
        """
        # 3 folds, 10 features
        # Feature 0 is consistently the highest (100), Feature 9 is lowest (10)
        per_fold_importances = [
            np.array([100, 90, 80, 70, 60, 50, 40, 30, 20, 10]),
            np.array([102, 92, 82, 72, 62, 52, 42, 32, 22, 12]),
            np.array([101, 91, 81, 71, 61, 51, 41, 31, 21, 11])
        ]
        
        result = calculate_cv_stability(per_fold_importances)
        
        # The top 5 features (indices 0-4) should be selected.
        # Their means should be roughly [101, 91, 81, 71, 61]
        expected_top_5_means = np.mean(per_fold_importances, axis=0)[:5]
        
        assert len(result['mean_importances']) == 5, \
            "Result must contain exactly 5 mean importances for top 5 features"
        assert np.allclose(result['mean_importances'], expected_top_5_means), \
            "Top 5 mean importances must match the first 5 features"

    def test_cv_stability_handles_zero_importance(self):
        """
        Verify behavior when some top features have zero importance.
        Avoids division by zero errors.
        """
        per_fold_importances = [
            np.array([100, 0, 0, 0, 0]),
            np.array([100, 0, 0, 0, 0]),
            np.array([100, 0, 0, 0, 0])
        ]
        
        result = calculate_cv_stability(per_fold_importances)
        
        # Mean of top 5: [100, 0, 0, 0, 0]
        # Mean of means: 20
        # Std of means: sqrt(((80)^2 + 4*(-20)^2)/4) = sqrt((6400 + 1600)/4) = sqrt(2000) ≈ 44.72
        # CV = 44.72 / 20 = 2.236
        # However, if std calculation results in 0 (e.g. all non-zero are same), check logic.
        # Here, values are 100, 0, 0, 0, 0.
        # Mean = 20.
        # Deviations: 80, -20, -20, -20, -20.
        # Sq Devs: 6400, 400, 400, 400, 400. Sum = 8000.
        # Var = 8000 / 4 = 2000. Std = 44.72.
        # CV = 2.236.
        
        assert result['cv_score'] > 0, "CV should be positive when variance exists"
        assert not np.isnan(result['cv_score']), "CV should not be NaN"

    def test_cv_stability_output_format(self):
        """
        Verify the output dictionary structure matches the expected schema.
        """
        per_fold_importances = [
            np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
            np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        ]
        
        result = calculate_cv_stability(per_fold_importances)
        
        required_keys = ['cv_score', 'top_5_features', 'mean_importances', 'std_importances']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
            
        assert isinstance(result['cv_score'], float), "cv_score must be float"
        assert isinstance(result['mean_importances'], (list, np.ndarray)), "mean_importances must be array-like"
        assert len(result['mean_importances']) == 5, "mean_importances must have 5 elements"
        
        # Verify it can be serialized to JSON (common requirement for reports)
        json_str = json.dumps(result, default=lambda x: float(x) if isinstance(x, np.floating) else str(x))
        assert json_str is not None, "Result must be JSON serializable"

    def test_cv_stability_vs_raw_cv(self):
        """
        Explicitly demonstrate the difference between:
        1. CV of (Mean of features across folds) -> CORRECT
        2. CV of (All raw values flattened) -> INCORRECT
        
        This ensures the implementation is not accidentally using the wrong logic.
        """
        per_fold_importances = [
            np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
            np.array([100.0, 200.0, 300.0, 400.0, 500.0]) # Large variance between folds
        ]
        
        result = calculate_cv_stability(per_fold_importances)
        
        # Correct logic:
        # Means: [55, 110, 165, 220, 275]
        # Mean of means: 165
        # Std of means (ddof=1): 82.5
        # CV_correct = 82.5 / 165 = 0.5
        
        # Incorrect logic (flattened):
        # Values: [10, 20, 30, 40, 50, 100, 200, 300, 400, 500]
        # Mean: 127
        # Std: ~168
        # CV_incorrect = 168 / 127 = 1.32
        
        # The result should be 0.5, not 1.32
        assert np.isclose(result['cv_score'], 0.5, rtol=1e-4), \
            f"CV logic error: got {result['cv_score']}, expected 0.5 (mean-across-folds logic)"
            
        # If the logic was wrong, it would be close to 1.32
        assert not np.isclose(result['cv_score'], 1.32, rtol=1e-1), \
            "CV calculation appears to be using raw flattened values instead of mean-across-folds"