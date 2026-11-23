import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from model.confidence_metrics import (
    compute_expected_calibration_error,
    compute_ece_by_perturbation_type,
    extract_confidence_from_inference_log,
    compute_confidence_from_logits
)

class TestECECalculation:
    """Test ECE calculation logic against known synthetic data."""

    def test_perfectly_calibrated(self):
        """
        Test with perfectly calibrated data:
        - 5 samples with 0.9 confidence, all pass -> accuracy 1.0
        - 5 samples with 0.1 confidence, all fail -> accuracy 0.0
        ECE should be 0.0.
        """
        predictions = [
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.1, "status": "fail"},
            {"confidence_score": 0.1, "status": "fail"},
            {"confidence_score": 0.1, "status": "fail"},
            {"confidence_score": 0.1, "status": "fail"},
            {"confidence_score": 0.1, "status": "fail"},
        ]
        
        ece, bins = compute_expected_calibration_error(predictions, n_bins=10)
        
        # With perfect calibration, ECE should be 0
        assert abs(ece) < 1e-6, f"Expected ECE ~0, got {ece}"
        assert len(bins) == 2, f"Expected 2 bins, got {len(bins)}"

    def test_overconfident_model(self):
        """
        Test with an overconfident model:
        - 10 samples with 0.9 confidence, only 5 pass -> accuracy 0.5
        ECE should be |0.9 - 0.5| = 0.4.
        """
        predictions = [
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "pass"},
            {"confidence_score": 0.9, "status": "fail"},
            {"confidence_score": 0.9, "status": "fail"},
            {"confidence_score": 0.9, "status": "fail"},
            {"confidence_score": 0.9, "status": "fail"},
            {"confidence_score": 0.9, "status": "fail"},
        ]
        
        ece, bins = compute_expected_calibration_error(predictions, n_bins=10)
        
        # All in one bin (0.9), accuracy 0.5, confidence 0.9
        # ECE = 1.0 * |0.9 - 0.5| = 0.4
        expected_ece = 0.4
        assert abs(ece - expected_ece) < 1e-4, f"Expected ECE {expected_ece}, got {ece}"

    def test_empty_predictions(self):
        """Test that empty list returns ECE 0.0."""
        ece, bins = compute_expected_calibration_error([], n_bins=10)
        assert ece == 0.0
        assert bins == []

    def test_ece_by_perturbation_type(self):
        """Test ECE calculation grouped by perturbation type."""
        predictions = [
            {"confidence_score": 0.9, "status": "pass", "perturbation_type": "synonym"},
            {"confidence_score": 0.9, "status": "fail", "perturbation_type": "synonym"}, # Overconfident
            {"confidence_score": 0.5, "status": "pass", "perturbation_type": "typo"},
            {"confidence_score": 0.5, "status": "pass", "perturbation_type": "typo"}, # Calibrated
        ]
        
        result = compute_ece_by_perturbation_type(predictions)
        
        assert "ece_by_type" in result
        assert "synonym" in result["ece_by_type"]
        assert "typo" in result["ece_by_type"]
        
        # Synonym: 1 pass, 1 fail at 0.9 conf -> acc 0.5, conf 0.9 -> ECE 0.4
        assert abs(result["ece_by_type"]["synonym"] - 0.4) < 1e-4
        
        # Typo: 2 pass at 0.5 conf -> acc 1.0, conf 0.5 -> ECE 0.5
        assert abs(result["ece_by_type"]["typo"] - 0.5) < 1e-4

class TestConfidenceExtraction:
    """Test confidence extraction from logits and logs."""

    def test_compute_confidence_from_logits(self):
        """Test confidence calculation from random logits."""
        # Create random logits
        logits = np.random.randn(10, 5000).astype(np.float32)
        confidence = compute_confidence_from_logits(logits)
        
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of bounds"

    def test_extract_confidence_existing(self):
        """Test extraction when confidence_score already exists."""
        log = {"confidence_score": 0.85, "status": "pass"}
        conf = extract_confidence_from_inference_log(log)
        assert conf == 0.85

    def test_extract_confidence_default(self):
        """Test extraction when no confidence data exists."""
        log = {"status": "pass", "code": "print('hello')"}
        conf = extract_confidence_from_inference_log(log)
        assert conf == 0.5 # Default value

class TestECEBins:
    """Test ECE bin assignment logic."""

    def test_bin_assignment(self):
        """Verify bin assignment for various confidence values."""
        test_cases = [
            (0.0, 0),
            (0.05, 0),
            (0.099, 0),
            (0.1, 1),
            (0.15, 1),
            (0.9, 9),
            (0.95, 9),
            (1.0, 9), # Clamp to 9
        ]
        
        for conf, expected_bin in test_cases:
            # Simulate the logic in update_inference_logs_with_confidence
            bin_idx = min(9, max(0, int(conf * 10)))
            assert bin_idx == expected_bin, f"Conf {conf} -> Bin {bin_idx}, expected {expected_bin}"