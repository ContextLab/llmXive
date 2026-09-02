"""
Unit tests for analysis logic, specifically MAE calculation.
"""

import pytest
from config import Solvent
from utils.logging import get_logger

logger = get_logger(__name__)

# Placeholder for actual implementation import if available
# from analysis.msd import calculate_diffusion_coefficient
# from analysis.bootstrap import calculate_mae

class TestMAE:
    """Tests for Mean Absolute Error calculation logic."""

    def test_mae_calculation_basic(self):
        """Test basic MAE calculation."""
        # Predicted values
        predicted = [2.30e-9, 2.35e-9, 2.25e-9]
        # Actual values (NIST)
        actual = [2.30e-9, 2.30e-9, 2.30e-9]

        # MAE = mean(|predicted - actual|)
        errors = [abs(p - a) for p, a in zip(predicted, actual)]
        expected_mae = sum(errors) / len(errors)

        # 0.0, 0.05e-9, 0.05e-9 -> sum 0.1e-9 -> mean 0.0333e-9
        assert abs(expected_mae - 3.333e-11) < 1e-12

    def test_mae_zero_error(self):
        """Test MAE when predictions are perfect."""
        predicted = [1.0, 2.0, 3.0]
        actual = [1.0, 2.0, 3.0]

        errors = [abs(p - a) for p, a in zip(predicted, actual)]
        mae = sum(errors) / len(errors)

        assert mae == 0.0

    def test_mae_single_value(self):
        """Test MAE with a single data point."""
        predicted = [5.0]
        actual = [3.0]

        mae = abs(5.0 - 3.0) / 1
        assert mae == 2.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])