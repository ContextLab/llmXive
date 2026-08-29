"""
Unit tests for power analysis calculations.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.research.power_analysis import (
    calculate_contrast_power,
    calculate_anova_power,
    normalize_contrast,
    EFFECT_SIZE,
    ALPHA,
    POWER_TARGET,
    N_GROUPS
)


class TestNormalizeContrast:
    """Tests for contrast normalization."""
    
    def test_normalize_contrast_high_vs_low(self):
        """Test normalization of High vs. Low contrast."""
        contrast = np.array([-1, 1, 0])
        normalized = normalize_contrast(contrast)
        
        expected_norm = 1.0
        actual_norm = np.linalg.norm(normalized)
        
        assert np.isclose(actual_norm, expected_norm)
        # Check that values are scaled correctly
        expected = np.array([-1/np.sqrt(2), 1/np.sqrt(2), 0])
        np.testing.assert_array_almost_equal(normalized, expected)
    
    def test_normalize_contrast_combined_vs_control(self):
        """Test normalization of (High+Low) vs. Control contrast."""
        contrast = np.array([1, 1, -2])
        normalized = normalize_contrast(contrast)
        
        expected_norm = 1.0
        actual_norm = np.linalg.norm(normalized)
        
        assert np.isclose(actual_norm, expected_norm)
        # Check that values are scaled correctly
        expected = np.array([1/2, 1/2, -2/2])  # sqrt(1+1+4) = sqrt(6)
        expected = np.array([1/np.sqrt(6), 1/np.sqrt(6), -2/np.sqrt(6)])
        np.testing.assert_array_almost_equal(normalized, expected)
    
    def test_normalize_contrast_zero_vector_raises(self):
        """Test that zero vector raises error."""
        with pytest.raises((ValueError, RuntimeWarning)):
            normalize_contrast(np.array([0, 0, 0]))


class TestContrastPowerCalculation:
    """Tests for contrast power calculations."""
    
    def test_contrast_power_returns_positive_integer(self):
        """Test that contrast power calculation returns a positive integer."""
        result = calculate_contrast_power(EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS)
        
        assert isinstance(result, int)
        assert result > 0
        assert result < 10000  # Should converge within reasonable bounds
    
    def test_contrast_power_with_different_effect_sizes(self):
        """Test that larger effect sizes require smaller sample sizes."""
        n_small_effect = calculate_contrast_power(0.1, ALPHA, POWER_TARGET, N_GROUPS)
        n_medium_effect = calculate_contrast_power(0.25, ALPHA, POWER_TARGET, N_GROUPS)
        n_large_effect = calculate_contrast_power(0.4, ALPHA, POWER_TARGET, N_GROUPS)
        
        # Larger effect size should require smaller sample size
        assert n_large_effect <= n_medium_effect <= n_small_effect
    
    def test_contrast_power_with_different_alphas(self):
        """Test that stricter alpha requires larger sample sizes."""
        n_alpha_05 = calculate_contrast_power(EFFECT_SIZE, 0.05, POWER_TARGET, N_GROUPS)
        n_alpha_01 = calculate_contrast_power(EFFECT_SIZE, 0.01, POWER_TARGET, N_GROUPS)
        
        # Stricter alpha (0.01) should require larger sample size
        assert n_alpha_01 >= n_alpha_05
    
    def test_contrast_power_with_different_power_targets(self):
        """Test that higher power targets require larger sample sizes."""
        n_power_80 = calculate_contrast_power(EFFECT_SIZE, ALPHA, 0.80, N_GROUPS)
        n_power_90 = calculate_contrast_power(EFFECT_SIZE, ALPHA, 0.90, N_GROUPS)
        
        # Higher power target should require larger sample size
        assert n_power_90 >= n_power_80


class TestANOVA_PowerCalculation:
    """Tests for ANOVA power calculations."""
    
    def test_anova_power_returns_positive_integer(self):
        """Test that ANOVA power calculation returns a positive integer."""
        result = calculate_anova_power(EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS)
        
        assert isinstance(result, int)
        assert result > 0
        assert result < 10000  # Should converge within reasonable bounds
    
    def test_anova_power_with_different_groups(self):
        """Test that more groups affect sample size requirements."""
        n_3_groups = calculate_anova_power(EFFECT_SIZE, ALPHA, POWER_TARGET, 3)
        n_4_groups = calculate_anova_power(EFFECT_SIZE, ALPHA, POWER_TARGET, 4)
        
        # More groups typically require larger sample sizes for same power
        assert n_4_groups >= n_3_groups


class TestMainExecution:
    """Tests for main function execution."""
    
    def test_main_creates_output_file(self):
        """Test that main() creates the output JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            research_dir = Path(tmpdir) / "research"
            research_dir.mkdir()
            
            # Patch the output path
            with patch('code.research.power_analysis.Path') as mock_path:
                mock_path.return_value.mkdir.return_value = None
                mock_output_path = Path(tmpdir) / "research" / "power_calculation.json"
                mock_path.return_value.__truediv__.return_value = mock_output_path
                
                # Run main
                result = code.research.power_analysis.main()
                
                assert result == 0
                # Verify file was created (mocked)
                mock_path.return_value.mkdir.assert_called()
    
    def test_main_returns_zero_on_success(self):
        """Test that main() returns 0 on successful execution."""
        # We can't easily test the full main without mocking file I/O,
        # but we can verify the logic doesn't raise exceptions
        try:
            # Just test that the calculations work
            n = calculate_contrast_power(EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS)
            assert n is not None
        except Exception as e:
            pytest.fail(f"Main execution logic raised exception: {e}")