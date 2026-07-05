"""
Unit tests for the power analysis logic in code/00_power_analysis.py.
"""
import pytest
import math
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import TARGET_N, ALPHA, EFFECT_SIZE_D
from code.utils.logger import setup_logger

# Import the functions to test
# We import from the module directly, handling the relative import issue in tests
import code._00_power_analysis as power_module

class TestDesignEffect:
    def test_design_effect_calculation(self):
        """Test that design effect is calculated correctly."""
        icc = 0.05
        avg_cluster_size = 10
        expected_de = 1 + (10 - 1) * 0.05
        assert expected_de == 1.45
        result = power_module.estimate_design_effect(icc, avg_cluster_size)
        assert result == expected_de

    def test_design_effect_zero_icc(self):
        """Test design effect when ICC is 0 (no clustering)."""
        result = power_module.estimate_design_effect(0.0, 10)
        assert result == 1.0

    def test_design_effect_high_icc(self):
        """Test design effect with high ICC."""
        result = power_module.estimate_design_effect(0.2, 20)
        # 1 + 19 * 0.2 = 1 + 3.8 = 4.8
        assert result == 4.8

class TestRequiredN:
    def test_required_n_calculation(self):
        """Test required N calculation with standard values."""
        # d=0.15, alpha=0.05, power=0.80, DE=1.45
        # Base N = 2 * ((1.96 + 0.84) / 0.15)^2 = 2 * (2.8/0.15)^2 = 2 * (18.66)^2 = 2 * 348.44 = 696.88
        # Adjusted N = 696.88 * 1.45 = 1010.4 -> 1011 per group
        # Total = 2022
        # Note: The exact values depend on the Z-scores used (1.96, 0.84)
        d = 0.15
        alpha = 0.05
        power = 0.80
        de = 1.45
        
        result = power_module.calculate_required_n_per_group(d, alpha, power, de)
        assert result > 0
        # Just check it's a reasonable number for d=0.15 (usually ~3500-4000 per group without DE)
        # With DE=1.45, it should be higher.
        assert result > 1000 

    def test_required_n_small_effect_size(self):
        """Test that smaller effect size requires larger N."""
        n_large_d = power_module.calculate_required_n_per_group(0.5, 0.05, 0.80, 1.0)
        n_small_d = power_module.calculate_required_n_per_group(0.1, 0.05, 0.80, 1.0)
        assert n_small_d > n_large_d

    def test_required_n_invalid_effect_size(self):
        """Test that invalid effect size raises error."""
        with pytest.raises(ValueError):
            power_module.calculate_required_n_per_group(0, 0.05, 0.80, 1.0)
        with pytest.raises(ValueError):
            power_module.calculate_required_n_per_group(-0.1, 0.05, 0.80, 1.0)

class TestRunPowerAnalysis:
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_pilot_data_exists(self, mock_open, mock_exists):
        """Test behavior when pilot data exists."""
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.read.return_value = "0.03" # ICC value
        mock_open.return_value = mock_file

        # Mock logger to avoid file writing in tests
        with patch.object(power_module, 'setup_logger') as mock_logger_setup:
            mock_logger = MagicMock()
            mock_logger_setup.return_value = mock_logger
            
            # We need to mock the TARGET_N to be very high so it passes
            with patch.object(power_module, 'TARGET_N', 20000):
                result = power_module.run_power_analysis()
                assert result is True
                # Verify log info about pilot data was called
                assert any("Pilot data found" in str(call) for call in mock_logger.info.call_args_list)

    @patch('pathlib.Path.exists')
    def test_no_pilot_data(self, mock_exists):
        """Test behavior when no pilot data exists (theoretical ICC)."""
        mock_exists.return_value = False

        with patch.object(power_module, 'setup_logger') as mock_logger_setup:
            mock_logger = MagicMock()
            mock_logger_setup.return_value = mock_logger
            
            with patch.object(power_module, 'TARGET_N', 20000):
                result = power_module.run_power_analysis()
                assert result is True
                # Verify theoretical rationale was logged
                rationale_logs = [str(call) for call in mock_logger.info.call_args_list]
                assert any("Rationale" in log for log in rationale_logs)
                assert any("Cialdini" in log for log in rationale_logs)

    @patch('pathlib.Path.exists')
    def test_power_insufficient(self, mock_exists):
        """Test behavior when power is insufficient."""
        mock_exists.return_value = False

        with patch.object(power_module, 'setup_logger') as mock_logger_setup:
            mock_logger = MagicMock()
            mock_logger_setup.return_value = mock_logger
            
            # Set target N very low to force failure
            with patch.object(power_module, 'TARGET_N', 100):
                result = power_module.run_power_analysis()
                assert result is False
                # Verify abort condition was logged
                assert any("ABORT" in str(call) for call in mock_logger.critical.call_args_list)