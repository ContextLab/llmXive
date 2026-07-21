import json
import os
import tempfile
from unittest.mock import patch

import numpy as np
import pytest
from scipy import stats

# Import the module under test
# Assuming the tests are run from the project root, adjust path if necessary
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss,
    compute_all_features,
    load_aligned_data,
)

# ---------------------------------------------------------------------------
# Unit Tests for Statistical Functions
# ---------------------------------------------------------------------------

class TestVarianceAndRange:
    def test_normal_distribution(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        var, rng = calculate_variance_and_range(values)
        # Numpy variance (ddof=0) for [1,2,3,4,5] is 2.0
        assert np.isclose(var, 2.0)
        assert np.isclose(rng, 4.0)

    def test_single_value(self):
        values = [5.0]
        var, rng = calculate_variance_and_range(values)
        assert var == 0.0
        assert rng == 0.0

    def test_empty_list(self):
        values = []
        var, rng = calculate_variance_and_range(values)
        assert var == 0.0
        assert rng == 0.0

    def test_constant_values(self):
        values = [3.0, 3.0, 3.0]
        var, rng = calculate_variance_and_range(values)
        assert var == 0.0
        assert rng == 0.0

class TestEntropy:
    def test_uniform_distribution(self):
        # Uniform distribution over 4 outcomes -> entropy = log(4)
        # Using softmax on [0,0,0,0] gives uniform probs
        values = [0.0, 0.0, 0.0, 0.0]
        ent = calculate_entropy(values)
        expected = np.log(4)
        assert np.isclose(ent, expected)

    def test_skewed_distribution(self):
        # One value dominates -> low entropy
        values = [10.0, 0.0, 0.0, 0.0]
        ent = calculate_entropy(values)
        # Should be close to 0
        assert ent < 1.0

    def test_negative_logits(self):
        values = [-1.0, -2.0, -3.0]
        ent = calculate_entropy(values)
        assert ent >= 0

    def test_constant_values(self):
        values = [5.0, 5.0, 5.0]
        ent = calculate_entropy(values)
        assert ent == 0.0

class TestSkewnessAndKurtosis:
    def test_normal_distribution(self):
        # Generate a known normal distribution
        np.random.seed(42)
        values = np.random.normal(0, 1, 1000).tolist()
        skew, kurt = calculate_skewness_and_kurtosis(values)
        # Skewness should be close to 0, Kurtosis (excess) close to 0
        assert np.isclose(skew, 0, atol=0.1)
        assert np.isclose(kurt, 0, atol=0.1)

    def test_skewed_distribution(self):
        # Exponential distribution is skewed
        values = np.random.exponential(1, 1000).tolist()
        skew, kurt = calculate_skewness_and_kurtosis(values)
        # Skewness > 0
        assert skew > 0

    def test_small_sample(self):
        values = [1.0, 2.0]
        skew, kurt = calculate_skewness_and_kurtosis(values)
        # Should handle gracefully
        assert isinstance(skew, float)
        assert isinstance(kurt, float)

    def test_constant_values(self):
        values = [5.0, 5.0, 5.0]
        skew, kurt = calculate_skewness_and_kurtosis(values)
        assert skew == 0.0
        assert kurt == 0.0

# ---------------------------------------------------------------------------
# Integration Tests for Per-Sample Stats
# ---------------------------------------------------------------------------

class TestPerSampleStats:
    def test_full_calculation(self):
        values = [1.0, 2.0, 3.0, 4.0]
        result = calculate_per_sample_stats(values, None) # Logger can be None for unit test if not used in logic
        
        assert "variance" in result
        assert "range" in result
        assert "entropy" in result
        assert "skewness" in result
        assert "kurtosis" in result
        
        # Check types
        for key, val in result.items():
            assert isinstance(val, float)

    def test_zero_variance_handling(self):
        values = [5.0, 5.0, 5.0]
        result = calculate_per_sample_stats(values, None)
        
        assert result["variance"] == 0.0
        assert result["entropy"] == 0.0
        assert result["skewness"] == 0.0
        assert result["kurtosis"] == 0.0

# ---------------------------------------------------------------------------
# Integration Tests for Global Entanglement
# ---------------------------------------------------------------------------

class TestGlobalEntanglement:
    def test_global_covariance(self):
        # Create a simple dataset: 3 samples, 2 dimensions
        # Sample 1: [1, 10]
        # Sample 2: [2, 20]
        # Sample 3: [3, 30]
        # Perfect correlation -> one dominant eigenvalue, one near zero
        data = [[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]
        
        eigenvalue = calculate_global_entanglement_score(data, None)
        
        assert eigenvalue > 0
        assert not np.isnan(eigenvalue)

    def test_insufficient_data(self):
        data = [[1.0, 2.0]] # Only 1 sample
        eigenvalue = calculate_global_entanglement_score(data, None)
        assert eigenvalue == 0.0

    def test_empty_data(self):
        eigenvalue = calculate_global_entanglement_score([], None)
        assert eigenvalue == 0.0

# ---------------------------------------------------------------------------
# Integration Tests for Fidelity Loss
# ---------------------------------------------------------------------------

class TestDimensionalFidelityLoss:
    def test_correct_loss_calculation(self):
        student = 0.8
        human = {"Alignment": 0.9, "Realism": 0.7}
        primary = "Alignment"
        
        loss = calculate_dimensional_fidelity_loss(student, human, primary, None)
        assert np.isclose(loss, 0.1)

    def test_missing_dimension_raises(self):
        student = 0.8
        human = {"Realism": 0.7}
        primary = "Alignment"
        
        with pytest.raises(KeyError):
            calculate_dimensional_fidelity_loss(student, human, primary, None)

# ---------------------------------------------------------------------------
# End-to-End Feature Computation Test
# ---------------------------------------------------------------------------

class TestComputeAllFeatures:
    def test_full_pipeline(self):
        # Create mock data
        mock_data = [
            {
                "sample_id": "s1",
                "teacher_logits": [1.0, 2.0, 3.0, 4.0],
                "student_scalar": 0.5,
                "human_annotations": {"Alignment": 0.6, "Realism": 0.4},
                "primary_dimension": "Alignment",
            },
            {
                "sample_id": "s2",
                "teacher_logits": [4.0, 3.0, 2.0, 1.0],
                "student_scalar": 0.4,
                "human_annotations": {"Alignment": 0.3, "Realism": 0.5},
                "primary_dimension": "Alignment",
            },
        ]
        
        # Mock logger
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
        
        features, eigenvalue = compute_all_features(mock_data, MockLogger())
        
        assert len(features) == 2
        assert features[0]["sample_id"] == "s1"
        assert "variance" in features[0]
        assert "entropy" in features[0]
        assert "dominant_eigenvalue" in features[0]
        assert "fidelity_loss" in features[0]
        
        # Check fidelity loss for s1: |0.5 - 0.6| = 0.1
        assert np.isclose(features[0]["fidelity_loss"], 0.1)

    def test_missing_annotation_excludes_sample(self):
        mock_data = [
            {
                "sample_id": "s1",
                "teacher_logits": [1.0, 2.0],
                "student_scalar": 0.5,
                "human_annotations": {}, # Missing primary dimension
                "primary_dimension": "Alignment",
            },
            {
                "sample_id": "s2",
                "teacher_logits": [1.0, 2.0],
                "student_scalar": 0.5,
                "human_annotations": {"Alignment": 0.5},
                "primary_dimension": "Alignment",
            },
        ]
        
        class MockLogger:
            def info(self, msg): pass
            def warning(self, msg): pass
            def error(self, msg): pass
        
        features, eigenvalue = compute_all_features(mock_data, MockLogger())
        
        # s1 should be excluded
        assert len(features) == 1
        assert features[0]["sample_id"] == "s2"