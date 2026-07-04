"""
Unit tests for metrics calculation in code/utils/metrics.py.
Specifically verifies that BLEU handles null references gracefully.
"""
import sys
import os

# Ensure the code directory is in the path to import utils.metrics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.metrics import bleu_score, f1_score


class TestBLEUNullHandling:
    """Tests for BLEU score calculation with null or empty inputs."""

    def test_bleu_with_empty_references(self):
        """Verify BLEU returns 0.0 when references list is empty."""
        prediction = ["this", "is", "a", "test"]
        references = []
        score = bleu_score(prediction, references)
        assert score == 0.0, "BLEU score should be 0.0 for empty references"

    def test_bleu_with_none_references(self):
        """Verify BLEU handles None references gracefully."""
        prediction = ["this", "is", "a", "test"]
        references = None
        score = bleu_score(prediction, references)
        assert score == 0.0, "BLEU score should be 0.0 for None references"

    def test_bleu_with_empty_prediction(self):
        """Verify BLEU returns 0.0 when prediction is empty."""
        prediction = []
        references = [["this", "is", "a", "test"]]
        score = bleu_score(prediction, references)
        assert score == 0.0, "BLEU score should be 0.0 for empty prediction"

    def test_bleu_with_both_empty(self):
        """Verify BLEU handles both prediction and references being empty."""
        prediction = []
        references = []
        score = bleu_score(prediction, references)
        assert score == 0.0, "BLEU score should be 0.0 when both are empty"

    def test_bleu_normal_case(self):
        """Verify BLEU works correctly for normal inputs."""
        prediction = ["the", "cat", "is", "on", "the", "mat"]
        references = [["the", "cat", "is", "on", "the", "mat"]]
        score = bleu_score(prediction, references)
        assert score == 1.0, "BLEU score should be 1.0 for identical sentences"


class TestF1NullHandling:
    """Tests for F1 score calculation with null or edge-case inputs."""

    def test_f1_with_zero_tp_fp_fn(self):
        """Verify F1 returns 0.0 when all counts are zero."""
        tp, fp, fn = 0, 0, 0
        score = f1_score(tp, fp, fn)
        assert score == 0.0, "F1 score should be 0.0 when tp=fp=fn=0"

    def test_f1_with_zero_tp(self):
        """Verify F1 returns 0.0 when true positives are zero."""
        tp, fp, fn = 0, 5, 5
        score = f1_score(tp, fp, fn)
        assert score == 0.0, "F1 score should be 0.0 when tp=0"

    def test_f1_normal_case(self):
        """Verify F1 works correctly for normal inputs."""
        tp, fp, fn = 5, 5, 5
        # Precision = 5/10 = 0.5, Recall = 5/10 = 0.5, F1 = 2 * (0.5*0.5)/(0.5+0.5) = 0.5
        score = f1_score(tp, fp, fn)
        assert score == 0.5, "F1 score calculation is incorrect"

    def test_f1_perfect_case(self):
        """Verify F1 returns 1.0 for perfect prediction."""
        tp, fp, fn = 10, 0, 0
        score = f1_score(tp, fp, fn)
        assert score == 1.0, "F1 score should be 1.0 for perfect prediction"


if __name__ == "__main__":
    import unittest
    unittest.main()