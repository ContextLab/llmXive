"""
Unit tests for analysis.py functions.
"""
import pytest
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from code.analysis import calculate_pairwise_cosine_similarity, run_hypothesis_test, generate_sensitivity_report

class TestCalculatePairwiseCosineSimilarity:
    def test_baseline_similarity_calculation(self):
        """Test that baseline similarities are calculated correctly."""
        vectors = [
            {"PairID": 1, "vector": [1.0, 0.0, 0.0], "type": "baseline"},
            {"PairID": 1, "vector": [0.0, 1.0, 0.0], "type": "baseline"},
            {"PairID": 2, "vector": [1.0, 1.0, 0.0], "type": "baseline"},
            {"PairID": 2, "vector": [1.0, 1.0, 0.0], "type": "baseline"},
        ]
        pair_ids = [1, 2]
        
        result = calculate_pairwise_cosine_similarity(vectors, pair_ids)
        
        assert "baseline" in result
        assert len(result["baseline"]) == 2
        
        # Pair 1: (1,0,0) vs (0,1,0) -> cos = 0
        assert abs(result["baseline"][0]) < 1e-6
        
        # Pair 2: (1,1,0) vs (1,1,0) -> cos = 1
        assert abs(result["baseline"][1] - 1.0) < 1e-6

    def test_perturbed_similarity_calculation(self):
        """Test that perturbed similarities are calculated correctly."""
        vectors = [
            {"PairID": 1, "vector": [0.9, 0.1, 0.0], "type": "perturbed", "sigma": 0.1},
            {"PairID": 1, "vector": [0.1, 0.9, 0.0], "type": "perturbed", "sigma": 0.1},
        ]
        pair_ids = [1]
        
        result = calculate_pairwise_cosine_similarity(vectors, pair_ids)
        
        assert "perturbed" in result
        assert 0.1 in result["perturbed"]
        assert len(result["perturbed"][0.1]) == 1
        
        # (0.9, 0.1) vs (0.1, 0.9) -> dot=0.18, norms=sqrt(0.82), cos=0.18/0.82 = 0.2195
        expected = 0.18 / 0.82
        assert abs(result["perturbed"][0.1][0] - expected) < 1e-4

    def test_missing_pair_id(self):
        """Test handling of vectors missing PairID."""
        vectors = [
            {"vector": [1.0, 0.0], "type": "baseline"}, # Missing PairID
            {"PairID": 1, "vector": [1.0, 0.0], "type": "baseline"},
            {"PairID": 1, "vector": [0.0, 1.0], "type": "baseline"},
        ]
        pair_ids = [1]
        
        # Should not crash, should skip missing PairID
        result = calculate_pairwise_cosine_similarity(vectors, pair_ids)
        assert len(result["baseline"]) == 1 # Only pair 1 is processed

    def test_empty_vectors(self):
        """Test handling of empty input."""
        result = calculate_pairwise_cosine_similarity([], [])
        assert result["baseline"] == []
        assert result["perturbed"] == {}

class TestRunHypothesisTest:
    def test_paired_t_test_normal_data(self):
        """Test Paired t-test selection for normal data."""
        # Generate normal data
        np.random.seed(42)
        baseline = np.random.normal(0.5, 0.1, 100)
        perturbed = np.random.normal(0.4, 0.1, 100)
        
        result = run_hypothesis_test(baseline.tolist(), perturbed.tolist())
        
        assert result["test_type"] == "paired_t_test"
        assert result["significant"] is True or result["significant"] is False
        assert result["p_value"] is not None
        assert result["statistic"] is not None

    def test_wilcoxon_non_normal_data(self):
        """Test Wilcoxon selection for non-normal data."""
        # Generate skewed data (exponential)
        baseline = np.random.exponential(0.5, 50)
        perturbed = np.random.exponential(0.6, 50)
        
        result = run_hypothesis_test(baseline.tolist(), perturbed.tolist())
        
        # With skewed data, Shapiro-Wilk should fail normality
        # So Wilcoxon should be selected
        assert result["test_type"] == "wilcoxon_signed_rank"
        assert result["p_value"] is not None

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        result = run_hypothesis_test([], [])
        assert "error" in result
        assert result["test_type"] is None

class TestGenerateSensitivityReport:
    def test_report_generation(self):
        """Test that a sensitivity report is generated correctly."""
        similarity_results = {
            "baseline": [0.5, 0.6, 0.7],
            "perturbed": {
                0.1: [0.4, 0.5, 0.6],
                0.2: [0.3, 0.4, 0.5]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("sigma,status\n0.1,passed\n0.2,failed\n")
            validity_log_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name
        
        try:
            report = generate_sensitivity_report(
                similarity_results,
                validity_log_path,
                output_path
            )
            
            assert "baseline_statistics" in report
            assert "perturbed_statistics" in report
            assert "hypothesis_tests" in report
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
                assert saved_report == report
        finally:
            os.remove(validity_log_path)
            os.remove(output_path)