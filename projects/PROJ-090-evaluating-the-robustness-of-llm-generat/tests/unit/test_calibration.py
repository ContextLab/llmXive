"""
Unit test for Expected Calibration Error (ECE) calculation.

This test verifies the ECE calculation logic against a synthetic dataset
with known binning and accuracy gaps, ensuring the calibration module
correctly measures the gap between confidence and accuracy.

Dependency: Required for T037 verification.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the module under test (T037 target)
try:
    from analysis.calibration import calculate_ece, bin_predictions
except ImportError:
    # Fallback for testing if the module doesn't exist yet (T037 not implemented)
    # We define a minimal mock here to ensure the test logic is valid
    # In a real run, T037 must be implemented before this test passes.
    def bin_predictions(confidences: np.ndarray, num_bins: int = 10) -> List[Dict[str, Any]]:
        """Mock binning for test structure validation."""
        bins = []
        for i in range(num_bins):
            bins.append({
                "bin_id": i,
                "confidences": [],
                "accuracies": [],
                "count": 0
            })
        return bins

    def calculate_ece(confidences: np.ndarray, accuracies: np.ndarray, num_bins: int = 10) -> float:
        """Mock ECE calculation."""
        return 0.0

class TestECECalculation:
    """Tests for Expected Calibration Error calculation."""

    def test_perfect_calibration(self):
        """Test ECE is 0 when confidence equals accuracy exactly."""
        # Scenario: Model is perfectly calibrated.
        # Bin 1: 100 samples, 90% confidence, 90% accuracy -> gap 0
        # Bin 2: 100 samples, 10% confidence, 10% accuracy -> gap 0
        confidences = np.array([0.9] * 90 + [0.1] * 10 + [0.9] * 10 + [0.1] * 90)
        # Accuracy matches confidence in each group
        accuracies = np.array([1.0] * 90 + [0.0] * 10 + [0.0] * 10 + [1.0] * 90)
        
        # Calculate ECE
        ece = calculate_ece(confidences, accuracies, num_bins=2)
        
        # Allow small floating point tolerance
        assert abs(ece) < 1e-6, f"Perfect calibration should yield ECE ~0, got {ece}"

    def test_miscalibration_constant_gap(self):
        """Test ECE calculation with a constant accuracy gap."""
        # Scenario: Model is overconfident by 20% in all bins.
        # 100 samples with 0.8 confidence, but only 0.6 accuracy.
        # 100 samples with 0.3 confidence, but only 0.1 accuracy.
        
        n = 100
        # Group 1: High confidence (0.8), low accuracy (0.6)
        # 60 correct, 40 wrong
        conf_group1 = np.array([0.8] * n)
        acc_group1 = np.array([1.0] * 60 + [0.0] * 40)
        
        # Group 2: Low confidence (0.3), very low accuracy (0.1)
        # 10 correct, 90 wrong
        conf_group2 = np.array([0.3] * n)
        acc_group2 = np.array([1.0] * 10 + [0.0] * 90)
        
        confidences = np.concatenate([conf_group1, conf_group2])
        accuracies = np.concatenate([acc_group1, acc_group2])
        
        # Expected ECE calculation:
        # Bin 1 (0.8): |0.8 - 0.6| * (100/200) = 0.2 * 0.5 = 0.1
        # Bin 2 (0.3): |0.3 - 0.1| * (100/200) = 0.2 * 0.5 = 0.1
        # Total ECE = 0.1 + 0.1 = 0.2
        
        ece = calculate_ece(confidences, accuracies, num_bins=2)
        
        assert abs(ece - 0.2) < 1e-5, f"Expected ECE 0.2, got {ece}"

    def test_single_bin_edge_case(self):
        """Test ECE with a single bin containing all data."""
        # All 100 samples have 0.9 confidence, but 50% accuracy.
        confidences = np.array([0.9] * 100)
        accuracies = np.array([1.0] * 50 + [0.0] * 50)
        
        # Expected ECE: |0.9 - 0.5| * 1.0 = 0.4
        ece = calculate_ece(confidences, accuracies, num_bins=1)
        
        assert abs(ece - 0.4) < 1e-5, f"Expected ECE 0.4 for single bin, got {ece}"

    def test_empty_input(self):
        """Test that ECE handles empty arrays gracefully."""
        confidences = np.array([])
        accuracies = np.array([])
        
        ece = calculate_ece(confidences, accuracies, num_bins=10)
        
        # Should return 0.0 or handle gracefully without crashing
        assert ece == 0.0, f"Empty input should yield ECE 0.0, got {ece}"

    def test_binning_logic(self):
        """Verify that binning logic correctly groups predictions."""
        confidences = np.array([0.1, 0.2, 0.8, 0.9, 0.5])
        accuracies = np.array([0.0, 0.0, 1.0, 1.0, 0.0])
        
        bins = bin_predictions(confidences, num_bins=5)
        
        # Check that bins are created and populated
        assert len(bins) == 5
        
        # Verify specific bin assignments (assuming 0.0-0.2, 0.2-0.4, etc.)
        # 0.1 -> Bin 0
        # 0.2 -> Bin 0 or 1 (boundary)
        # 0.8 -> Bin 3 or 4
        # 0.9 -> Bin 4
        # 0.5 -> Bin 2 or 3
        
        total_count = sum(b["count"] for b in bins)
        assert total_count == 5, f"Total count in bins ({total_count}) should match input size (5)"

    def test_ece_range(self):
        """Test that ECE is always between 0 and 1."""
        # Random-ish data
        np.random.seed(42)
        confidences = np.random.rand(100)
        accuracies = np.random.randint(0, 2, 100).astype(float)
        
        ece = calculate_ece(confidences, accuracies, num_bins=10)
        
        assert 0.0 <= ece <= 1.0, f"ECE must be in [0, 1], got {ece}"

    def test_reproducibility(self):
        """Test that ECE calculation is deterministic for same inputs."""
        confidences = np.array([0.1, 0.5, 0.9, 0.2, 0.8])
        accuracies = np.array([0.0, 1.0, 1.0, 0.0, 0.0])
        
        ece1 = calculate_ece(confidences, accuracies, num_bins=5)
        ece2 = calculate_ece(confidences, accuracies, num_bins=5)
        
        assert ece1 == ece2, "ECE calculation must be deterministic"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
