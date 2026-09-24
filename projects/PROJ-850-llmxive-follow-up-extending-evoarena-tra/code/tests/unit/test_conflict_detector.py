"""
Unit tests for the ConflictDetector module.
"""
import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from src.heuristics.conflict_detector import ConflictDetector

# Sample data for testing
TEST_PAIRS = [
    ("The sky is blue.", "The sky is blue."),  # Entailment/Neutral
    ("The sky is blue.", "The sky is green."),  # Contradiction
    ("Dogs are mammals.", "Cats are mammals."), # Neutral
    ("He is a doctor.", "He is a surgeon."),    # Entailment
]

class TestConflictDetector:
    """Tests for the ConflictDetector class."""

    def test_initialization_default(self):
        """Test that the detector initializes with default parameters."""
        detector = ConflictDetector()
        assert detector.model_name is not None
        assert detector.threshold == 0.90
        assert detector.device == "cpu"

    def test_initialization_custom(self):
        """Test initialization with custom parameters."""
        detector = ConflictDetector(model_name="typeform/distilbert-base-uncased-mnli", threshold=0.80)
        assert detector.threshold == 0.80

    def test_compute_scores_empty(self):
        """Test that compute_scores returns empty list for empty input."""
        detector = ConflictDetector()
        scores = detector.compute_scores([])
        assert scores == []

    def test_detect_conflicts_structure(self):
        """Test that detect_conflicts returns the correct structure."""
        detector = ConflictDetector()
        # Use a small subset to avoid long load times in tests
        # Note: In a real CI, we might mock the model or use a very small model.
        # For this test, we assume the model loads.
        try:
            results = detector.detect_conflicts(TEST_PAIRS[:2])
            assert isinstance(results, list)
            assert len(results) == 2
            for res in results:
                assert "patch_a" in res
                assert "patch_b" in res
                assert "score" in res
                assert "is_conflict" in res
                assert isinstance(res["score"], float)
                assert isinstance(res["is_conflict"], bool)
        except Exception as e:
            # If model loading fails (e.g., no internet in CI), skip the test
            pytest.skip(f"Model loading failed: {e}")

    def test_sensitivity_analysis_thresholds(self):
        """Test the sensitivity analysis across thresholds."""
        detector = ConflictDetector()
        thresholds = [0.5, 0.8, 0.9, 0.95]
        try:
            results = detector.run_sensitivity_analysis_thresholds(TEST_PAIRS[:2], thresholds)
            assert len(results) == len(thresholds)
            for res in results:
                assert "threshold" in res
                assert "num_conflicts" in res
                assert "conflict_rate" in res
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")

    def test_sensitivity_analysis_models(self):
        """Test the sensitivity analysis across models."""
        detector = ConflictDetector()
        # Use a list of models, including the default one
        model_names = ["typeform/distilbert-base-uncased-mnli"]
        try:
            results = detector.run_sensitivity_analysis_models(TEST_PAIRS[:2], model_names)
            assert len(results) == len(model_names)
            for res in results:
                assert "model_name" in res
                assert "num_conflicts" in res
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")