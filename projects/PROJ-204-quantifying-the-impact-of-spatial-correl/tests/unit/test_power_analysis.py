"""
Unit tests for power analysis module (T033).
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
import tempfile
import os

from modeling.power_analysis import (
    calculate_power_correlation,
    calculate_min_sample_size,
    evaluate_sample_adequacy,
    run_power_analysis
)
from utils.config import Config


class TestCalculatePowerCorrelation:
    """Tests for calculate_power_correlation function."""

    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases."""
        rho = 0.5
        power_n20 = calculate_power_correlation(20, rho)
        power_n50 = calculate_power_correlation(50, rho)
        power_n100 = calculate_power_correlation(100, rho)
        
        assert power_n20 < power_n50 < power_n100

    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size increases."""
        n = 50
        power_rho03 = calculate_power_correlation(n, 0.3)
        power_rho05 = calculate_power_correlation(n, 0.5)
        power_rho07 = calculate_power_correlation(n, 0.7)
        
        assert power_rho03 < power_rho05 < power_rho07

    def test_power_near_alpha_for_null_effect(self):
        """When rho=0, power should be approximately alpha."""
        n = 100
        power = calculate_power_correlation(n, 0.0, alpha=0.05)
        # Power for null effect should be close to alpha (Type I error rate)
        assert 0.04 <= power <= 0.06

    def test_power_near_one_for_large_effect(self):
        """Large effect sizes should yield power near 1."""
        n = 100
        power = calculate_power_correlation(n, 0.8)
        assert power > 0.95

    def test_insufficient_sample_size(self):
        """Sample size < 3 should return 0 power."""
        power = calculate_power_correlation(2, 0.5)
        assert power == 0.0

    def test_one_sided_greater_test(self):
        """Test one-sided greater alternative."""
        n = 50
        power_two_sided = calculate_power_correlation(n, 0.5, alternative="two-sided")
        power_greater = calculate_power_correlation(n, 0.5, alternative="greater")
        
        # One-sided should have higher power for positive rho
        assert power_greater > power_two_sided

    def test_invalid_alternative(self):
        """Invalid alternative should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_power_correlation(50, 0.5, alternative="invalid")


class TestCalculateMinSampleSize:
    """Tests for calculate_min_sample_size function."""

    def test_returns_reasonable_sample_size(self):
        """Should return a reasonable sample size for typical parameters."""
        n = calculate_min_sample_size(rho=0.5, power=0.8, alpha=0.05)
        assert 15 <= n <= 50  # Typical range for medium effect

    def test_requires_larger_sample_for_higher_power(self):
        """Higher power should require larger sample size."""
        n_80 = calculate_min_sample_size(rho=0.5, power=0.8)
        n_90 = calculate_min_sample_size(rho=0.5, power=0.9)
        
        assert n_90 > n_80

    def test_requires_larger_sample_for_smaller_effect(self):
        """Smaller effect size should require larger sample size."""
        n_50 = calculate_min_sample_size(rho=0.5, power=0.8)
        n_30 = calculate_min_sample_size(rho=0.3, power=0.8)
        
        assert n_30 > n_50

    def test_minimum_sample_is_three(self):
        """Should never return less than 3."""
        n = calculate_min_sample_size(rho=0.99, power=0.5)
        assert n >= 3


class TestEvaluateSampleAdequacy:
    """Tests for evaluate_sample_adequacy function."""

    def test_adequate_sample(self):
        """Sample above threshold should be adequate."""
        config = Config(min_sample_count=30)
        result = evaluate_sample_adequacy(50, config.to_dict())
        
        assert result['is_adequate'] is True
        assert result['flag'] == 'definitive'

    def test_inadequate_sample(self):
        """Sample below threshold should be inadequate."""
        config = Config(min_sample_count=30)
        result = evaluate_sample_adequacy(20, config.to_dict())
        
        assert result['is_adequate'] is False
        assert result['flag'] == 'non-definitive'
        assert "non-definitive" in result['message']

    def test_power_calculation_with_rho(self):
        """Should calculate power when rho_estimate is provided."""
        config = Config(min_sample_count=30)
        result = evaluate_sample_adequacy(50, config.to_dict(), rho_estimate=0.5)
        
        assert 'power' in result
        assert result['power'] > 0
        assert result['power'] <= 1.0

    def test_default_min_sample_count(self):
        """Should use default min_sample_count when config not provided."""
        with patch('modeling.power_analysis.get_config') as mock_get_config:
            mock_get_config.return_value = {"min_sample_count": 30}
            result = evaluate_sample_adequacy(25)
            
            assert result['min_required'] == 30
            assert result['is_adequate'] is False


class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""

    def test_writes_output_file(self):
        """Should write results to specified output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock correlation results
            corr_path = Path(tmpdir) / "correlation_results.csv"
            corr_df = pd.DataFrame({
                'metric': ['Pb-PCE', 'I-PCE', 'MA-PCE'],
                'correlation': [0.45, -0.32, 0.12],
                'p_value': [0.01, 0.03, 0.45],
                'n': [40, 40, 40]
            })
            corr_df.to_csv(corr_path, index=False)
            
            output_path = Path(tmpdir) / "power_analysis.csv"
            
            with patch('modeling.power_analysis.get_config') as mock_config:
                mock_config.return_value = {"min_sample_count": 30}
                result = run_power_analysis(
                    str(corr_path),
                    str(output_path)
                )
                
                assert output_path.exists()
                assert result['summary']['actual_count'] == 40

    def test_handles_missing_file(self):
        """Should return error when correlation file not found."""
        with patch('modeling.power_analysis.get_config') as mock_config:
            mock_config.return_value = {}
            result = run_power_analysis(
                "/nonexistent/path.csv",
                "/output/path.csv"
            )
            
            assert result['status'] == 'failed'
            assert 'Missing correlation results' in result['reason']

    def test_sets_flag_for_small_samples(self):
        """Should set 'non-definitive' flag for small samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            corr_path = Path(tmpdir) / "correlation_results.csv"
            corr_df = pd.DataFrame({
                'metric': ['Pb-PCE'],
                'correlation': [0.45],
                'p_value': [0.01],
                'n': [15]
            })
            corr_df.to_csv(corr_path, index=False)
            
            output_path = Path(tmpdir) / "power_analysis.csv"
            
            with patch('modeling.power_analysis.get_config') as mock_config:
                mock_config.return_value = {"min_sample_count": 30}
                result = run_power_analysis(
                    str(corr_path),
                    str(output_path)
                )
                
                assert result['summary']['flag'] == 'non-definitive'
                
                # Verify output file has correct flag
                output_df = pd.read_csv(output_path)
                assert all(output_df['flag'] == 'non-definitive')
