import os
import sys
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from evaluation.stats import (
    wilcoxon_signed_rank_test,
    calculate_vif,
    sensitivity_analysis_sweep
)

class TestWilcoxonSignedRank:
    def test_wilcoxon_two_sided(self):
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.5, 2.5, 3.5, 4.5, 5.5]
        
        result = wilcoxon_signed_rank_test(group1, group2, alternative="two-sided")
        
        assert "statistic" in result
        assert "p_value" in result
        assert "significant_at_0.05" in result
        assert isinstance(result["statistic"], float)
        assert isinstance(result["p_value"], float)

    def test_wilcoxon_different_lengths(self):
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0]
        
        with pytest.raises(ValueError):
            wilcoxon_signed_rank_test(group1, group2)

class TestCalculateVIF:
    def test_vif_no_collinearity(self):
        # Orthogonal features
        X = np.array([
            [1, 0],
            [0, 1],
            [1, 1],
            [0, 0],
            [2, 2]
        ])
        
        vif_results = calculate_vif(X)
        
        assert len(vif_results) == 2
        # VIF should be close to 1 for orthogonal features
        for vif_val in vif_results.values():
            assert vif_val < 2.0  # Threshold for low collinearity

    def test_vif_perfect_collinearity(self):
        # Perfectly collinear features
        X = np.array([
            [1, 1],
            [2, 2],
            [3, 3],
            [4, 4],
            [5, 5]
        ])
        
        vif_results = calculate_vif(X)
        
        # At least one feature should have infinite or very high VIF
        high_vif_count = sum(1 for v in vif_results.values() if np.isinf(v) or v > 100)
        assert high_vif_count > 0

    def test_vif_feature_names(self):
        X = np.random.rand(20, 3)
        names = ["A", "B", "C"]
        
        vif_results = calculate_vif(X, feature_names=names)
        
        assert set(vif_results.keys()) == set(names)

class TestSensitivityAnalysisSweep:
    def test_sweep_basic(self):
        cv_results = {
            "fold_results": [
                {"r2": 0.20},
                {"r2": 0.30},
                {"r2": 0.40},
                {"r2": 0.25},
                {"r2": 0.35}
            ]
        }
        
        thresholds = [0.25, 0.30, 0.35]
        result = sensitivity_analysis_sweep(cv_results, thresholds=thresholds)
        
        assert "results" in result
        assert "stability_metric" in result
        assert len(result["results"]) == len(thresholds)
        
        # Check specific rates
        # Threshold 0.25: 4 out of 5 > 0.25 (0.30, 0.40, 0.35, 0.25 is not > 0.25, so 3? Wait: 0.30, 0.40, 0.35 are > 0.25. 0.25 is not. 0.20 is not. So 3/5 = 0.6)
        # Let's re-verify logic: "predictions where R² > threshold"
        # 0.20 > 0.25? No. 0.30 > 0.25? Yes. 0.40 > 0.25? Yes. 0.25 > 0.25? No. 0.35 > 0.25? Yes. -> 3/5 = 0.6
        res_025 = next(r for r in result["results"] if r["threshold"] == 0.25)
        assert abs(res_025["successful_prediction_rate"] - 0.6) < 1e-6

    def test_sweep_empty_scores(self):
        cv_results = {"fold_results": []}
        result = sensitivity_analysis_sweep(cv_results, thresholds=[0.5])
        
        assert result["results"][0]["successful_prediction_rate"] == 0.0
        assert result["stability_metric"] == 0.0