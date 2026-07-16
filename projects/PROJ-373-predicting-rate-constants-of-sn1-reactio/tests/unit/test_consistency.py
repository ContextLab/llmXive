import pytest
import numpy as np
from scipy.stats import kendalltau
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.consistency import compute_kendall_tau_consistency, generate_consistency_report

class TestConsistencyMetrics:
    """Test cases for SHAP consistency analysis functions."""

    def test_kendall_tau_identical_rankings(self):
        """Test that identical rankings yield perfect correlation."""
        rankings = [
            [0, 1, 2, 3, 4],
            [0, 1, 2, 3, 4],
            [0, 1, 2, 3, 4]
        ]
        result = compute_kendall_tau_consistency(rankings)
        assert result == 1.0, "Identical rankings should have Kendall's Tau = 1.0"

    def test_kendall_tau_opposite_rankings(self):
        """Test that completely opposite rankings yield negative correlation."""
        rankings = [
            [0, 1, 2, 3, 4],
            [4, 3, 2, 1, 0]
        ]
        result = compute_kendall_tau_consistency(rankings)
        # For completely reversed rankings, tau should be -1.0
        assert result < -0.9, "Opposite rankings should have negative Kendall's Tau"

    def test_kendall_tau_random_rankings(self):
        """Test that random rankings yield moderate correlation."""
        rankings = [
            [0, 1, 2, 3, 4],
            [2, 0, 4, 1, 3],
            [1, 3, 0, 4, 2]
        ]
        result = compute_kendall_tau_consistency(rankings)
        # Should be between -1 and 1
        assert -1.0 <= result <= 1.0

    def test_single_ranking(self):
        """Test that a single ranking returns perfect consistency."""
        rankings = [[0, 1, 2, 3, 4]]
        result = compute_kendall_tau_consistency(rankings)
        assert result == 1.0, "Single ranking should have perfect consistency"

    def test_empty_rankings(self):
        """Test that empty rankings list returns 1.0."""
        rankings = []
        result = compute_kendall_tau_consistency(rankings)
        assert result == 1.0, "Empty rankings should return 1.0"

    def test_report_generation(self, tmp_path):
        """Test that the consistency report is generated correctly."""
        seeds = [42, 123, 456]
        results = [
            {'seed': 42, 'r2': 0.85, 'mae': 0.12, 'model_path': 'model1.pt'},
            {'seed': 123, 'r2': 0.83, 'mae': 0.14, 'model_path': 'model2.pt'},
            {'seed': 456, 'r2': 0.84, 'mae': 0.13, 'model_path': 'model3.pt'}
        ]
        rankings = [
            [0, 1, 2, 3, 4],
            [0, 1, 3, 2, 4],
            [0, 2, 1, 3, 4]
        ]
        consistency_metric = 0.85
        output_path = tmp_path / "test_report.md"

        generate_consistency_report(
            seeds=seeds,
            results=results,
            rankings=rankings,
            consistency_metric=consistency_metric,
            output_path=output_path,
            logger=None  # Mock logger for testing
        )

        # Check that file was created
        assert output_path.exists(), "Report file should be created"

        # Check file content
        content = output_path.read_text()
        assert "# SHAP Consistency Report" in content
        assert "Kendall's Tau" in content
        assert "0.85" in content
        assert "42" in content
        assert "123" in content
        assert "456" in content

    def test_report_with_failed_training(self, tmp_path):
        """Test report generation when some training runs fail."""
        seeds = [42, 123, 456]
        results = [
            {'seed': 42, 'r2': 0.85, 'mae': 0.12, 'model_path': 'model1.pt'},
            None,  # Failed training
            {'seed': 456, 'r2': 0.84, 'mae': 0.13, 'model_path': 'model3.pt'}
        ]
        rankings = [
            [0, 1, 2, 3, 4],
            [0, 1, 3, 2, 4]
        ]
        consistency_metric = 0.85
        output_path = tmp_path / "test_report.md"

        generate_consistency_report(
            seeds=seeds,
            results=results,
            rankings=rankings,
            consistency_metric=consistency_metric,
            output_path=output_path,
            logger=None
        )

        content = output_path.read_text()
        assert "Failed" in content
        assert "42" in content
        assert "456" in content

    def test_stability_thresholds(self):
        """Test that different consistency levels are correctly identified."""
        # High stability
        rankings_high = [[0, 1, 2, 3, 4]] * 5
        tau_high = compute_kendall_tau_consistency(rankings_high)
        assert tau_high == 1.0

        # Moderate stability
        rankings_mod = [
            [0, 1, 2, 3, 4],
            [1, 0, 2, 3, 4],
            [0, 2, 1, 3, 4]
        ]
        tau_mod = compute_kendall_tau_consistency(rankings_mod)
        assert 0.5 <= tau_mod < 1.0

        # Low stability
        rankings_low = [
            [0, 1, 2, 3, 4],
            [4, 3, 2, 1, 0],
            [2, 3, 0, 1, 4]
        ]
        tau_low = compute_kendall_tau_consistency(rankings_low)
        assert tau_low < 0.5
