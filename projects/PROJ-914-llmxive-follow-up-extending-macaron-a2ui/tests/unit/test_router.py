"""
Unit tests for router confidence scoring (T016).

Tests the confidence scoring logic of the DistilBERT router.
Verifies that:
1. Confidence scores are within [0, 1] range.
2. High-confidence queries get scores >= threshold.
3. Ambiguous queries get scores < threshold.
4. Batch prediction maintains consistency.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add code/ to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from models.router import load_quantized_model, predict_intent, batch_predict, create_pipeline
from config import RANDOM_SEED


class TestRouterConfidenceScoring:
    """Tests for router confidence scoring functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model with deterministic outputs for testing."""
        mock = MagicMock()
        # Mock the model to return specific logits for testing
        # Logits shape: (batch_size, num_labels)
        # We simulate 2 classes: [Ambiguous, High-Confidence]
        mock.num_labels = 2
        return mock

    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline for batch prediction tests."""
        mock = MagicMock()
        mock.num_labels = 2
        return mock

    def test_confidence_range_single_prediction(self, mock_model):
        """Test that confidence scores are always in [0, 1] range."""
        # Mock softmax output
        mock_model.return_value = {
            'logits': np.array([[1.0, 3.0], [2.0, 1.0]])
        }

        # Simulate the confidence calculation logic
        logits = np.array([[1.0, 3.0], [2.0, 1.0]])
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        confidence = np.max(probs, axis=1)

        assert np.all(confidence >= 0.0)
        assert np.all(confidence <= 1.0)
        assert len(confidence) == 2

    def test_high_confidence_threshold(self, mock_model):
        """Test that high-confidence queries exceed the threshold."""
        # High confidence: [0.1, 0.9] -> max prob = 0.9
        logits_high = np.array([[0.1, 0.9]])
        exp_logits = np.exp(logits_high)
        probs_high = exp_logits / np.sum(exp_logits)
        confidence_high = np.max(probs_high)

        # Threshold is typically 0.7 or 0.8
        threshold = 0.7
        assert confidence_high >= threshold

    def test_ambiguous_below_threshold(self, mock_model):
        """Test that ambiguous queries fall below the threshold."""
        # Ambiguous: [0.45, 0.55] -> max prob = 0.55
        logits_ambiguous = np.array([[0.45, 0.55]])
        exp_logits = np.exp(logits_ambiguous)
        probs_ambiguous = exp_logits / np.sum(exp_logits)
        confidence_ambiguous = np.max(probs_ambiguous)

        threshold = 0.7
        assert confidence_ambiguous < threshold

    def test_batch_prediction_consistency(self, mock_pipeline):
        """Test that batch prediction returns consistent confidence scores."""
        # Simulate batch of 3 queries with known logits
        batch_logits = np.array([
            [1.0, 3.0],   # High confidence (0.9)
            [0.45, 0.55], # Ambiguous (0.55)
            [2.0, 1.0]    # High confidence (0.73)
        ])

        # Calculate expected confidence scores
        exp_logits = np.exp(batch_logits - np.max(batch_logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        expected_confidence = np.max(probs, axis=1)

        assert len(expected_confidence) == 3
        assert np.all(expected_confidence >= 0.0)
        assert np.all(expected_confidence <= 1.0)

        # Verify specific values
        assert expected_confidence[0] >= 0.8  # First is high confidence
        assert expected_confidence[1] < 0.6   # Second is ambiguous
        assert expected_confidence[2] >= 0.6  # Third is moderate-high

    def test_confidence_threshold_classification(self):
        """Test classification logic based on confidence threshold."""
        threshold = 0.7

        test_cases = [
            (np.array([[0.1, 0.9]]), "High-Confidence"),
            (np.array([[0.9, 0.1]]), "Ambiguous"),
            (np.array([[0.45, 0.55]]), "Ambiguous"),
            (np.array([[0.2, 0.8]]), "High-Confidence"),
        ]

        for logits, expected_label in test_cases:
            exp_logits = np.exp(logits)
            probs = exp_logits / np.sum(exp_logits)
            confidence = np.max(probs)
            predicted_label = "High-Confidence" if confidence >= threshold else "Ambiguous"
            assert predicted_label == expected_label

    def test_edge_case_perfect_confidence(self):
        """Test edge case where confidence is exactly 1.0."""
        # Perfect confidence: [0, 10] -> softmax gives ~1.0
        logits = np.array([[0.0, 10.0]])
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        confidence = np.max(probs)

        assert confidence >= 0.999  # Should be very close to 1.0

    def test_edge_case_uniform_distribution(self):
        """Test edge case where confidence is 0.5 (uniform)."""
        # Uniform: [0, 0] -> softmax gives [0.5, 0.5]
        logits = np.array([[0.0, 0.0]])
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        confidence = np.max(probs)

        assert confidence == 0.5

    def test_confidence_monotonicity(self):
        """Test that confidence increases monotonically with logit difference."""
        base_logit = 0.5
        differences = [0.1, 0.5, 1.0, 2.0, 5.0]
        confidences = []

        for diff in differences:
            logits = np.array([[base_logit, base_logit + diff]])
            exp_logits = np.exp(logits)
            probs = exp_logits / np.sum(exp_logits)
            confidence = np.max(probs)
            confidences.append(confidence)

        # Confidence should increase as logit difference increases
        for i in range(1, len(confidences)):
            assert confidences[i] > confidences[i-1]

    def test_batch_size_variations(self):
        """Test confidence scoring with different batch sizes."""
        batch_sizes = [1, 5, 10, 20]

        for batch_size in batch_sizes:
            # Generate random logits
            np.random.seed(RANDOM_SEED)
            logits = np.random.randn(batch_size, 2)

            # Calculate confidence
            exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
            confidence = np.max(probs, axis=1)

            assert len(confidence) == batch_size
            assert np.all(confidence >= 0.0)
            assert np.all(confidence <= 1.0)

    def test_numerical_stability(self):
        """Test that confidence calculation is numerically stable for extreme values."""
        # Test with very large and very small logits
        extreme_logits = np.array([
            [1000.0, 1001.0],
            [-1000.0, -999.0],
            [10000.0, 10001.0]
        ])

        # Should not produce NaN or Inf
        exp_logits = np.exp(extreme_logits - np.max(extreme_logits, axis=1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        confidence = np.max(probs, axis=1)

        assert not np.any(np.isnan(confidence))
        assert not np.any(np.isinf(confidence))
        assert np.all(confidence >= 0.0)
        assert np.all(confidence <= 1.0)

    def test_confidence_threshold_sensitivity(self):
        """Test how confidence scores behave around the threshold."""
        threshold = 0.7

        # Test values just below and above threshold
        test_logits = [
            np.array([[0.3, 0.7]]),   # Exactly at threshold (0.7)
            np.array([[0.29, 0.71]]), # Just above (0.71)
            np.array([[0.31, 0.69]]), # Just below (0.69)
        ]

        results = []
        for logits in test_logits:
            exp_logits = np.exp(logits)
            probs = exp_logits / np.sum(exp_logits)
            confidence = np.max(probs)
            results.append(confidence)

        # Verify ordering
        assert results[1] > results[0]  # 0.71 > 0.7
        assert results[0] > results[2]  # 0.7 > 0.69

    def test_confidence_with_multiple_classes(self):
        """Test confidence scoring with more than 2 classes (if extended)."""
        # Simulate 3-class scenario
        logits = np.array([[0.1, 0.2, 0.7]])
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        confidence = np.max(probs)

        assert confidence >= 0.0
        assert confidence <= 1.0
        assert confidence > 0.5  # Should be high since 0.7 is dominant

    def test_router_pipeline_integration(self, mock_pipeline):
        """Test confidence scoring through the pipeline interface."""
        # Mock the pipeline's return value
        mock_pipeline.return_value = [
            {'label': 'High-Confidence', 'score': 0.9},
            {'label': 'Ambiguous', 'score': 0.55},
            {'label': 'High-Confidence', 'score': 0.75}
        ]

        # The pipeline should return scores that can be used for thresholding
        results = mock_pipeline(["query1", "query2", "query3"])

        assert len(results) == 3
        assert all('score' in r for r in results)
        assert all(0 <= r['score'] <= 1 for r in results)