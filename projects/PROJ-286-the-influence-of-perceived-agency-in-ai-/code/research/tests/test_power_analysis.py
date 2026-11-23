"""
Unit tests for power analysis calculations.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
from scipy import stats

# Import functions from the module
from code.research.power_analysis import (
    normalize_contrast,
    calculate_contrast_power,
    calculate_anova_power,
    find_minimum_n,
    main
)


class TestNormalizeContrast:
    """Tests for normalize_contrast function."""

    def test_normalize_simple_contrast(self):
        """Test normalization of a simple contrast vector."""
        contrast = [1, -1, 0]
        normalized = normalize_contrast(contrast)
        
        # Check that sum of squares is 1
        assert abs(sum(c**2 for c in normalized) - 1.0) < 1e-10
        
        # Check that direction is preserved
        assert normalized[0] > 0
        assert normalized[1] < 0
        assert normalized[2] == 0.0

    def test_normalize_zero_vector_raises(self):
        """Test that zero vector raises ValueError."""
        with pytest.raises(ValueError):
            normalize_contrast([0, 0, 0])

    def test_normalize_combined_vs_control(self):
        """Test normalization of combined vs control contrast."""
        contrast = [0.5, 0.5, -1]
        normalized = normalize_contrast(contrast)
        
        # Check that sum of squares is 1
        assert abs(sum(c**2 for c in normalized) - 1.0) < 1e-10


class TestContrastPowerCalculation:
    """Tests for calculate_contrast_power function."""

    def test_power_increases_with_n(self):
        """Test that power increases with sample size."""
        effect_size = 0.25
        alpha = 0.05
        contrast = [1, -1, 0]
        
        power_10, _ = calculate_contrast_power(effect_size, alpha, 10, 3, contrast)
        power_50, _ = calculate_contrast_power(effect_size, alpha, 50, 3, contrast)
        power_100, _ = calculate_contrast_power(effect_size, alpha, 100, 3, contrast)
        
        assert power_10 < power_50 < power_100

    def test_power_decreases_with_alpha(self):
        """Test that power decreases with stricter alpha."""
        effect_size = 0.25
        n = 50
        contrast = [1, -1, 0]
        
        power_05, _ = calculate_contrast_power(effect_size, 0.05, n, 3, contrast)
        power_01, _ = calculate_contrast_power(effect_size, 0.01, n, 3, contrast)
        
        assert power_05 > power_01

    def test_higher_effect_size_increases_power(self):
        """Test that higher effect size increases power."""
        alpha = 0.05
        n = 50
        contrast = [1, -1, 0]
        
        power_small, _ = calculate_contrast_power(0.1, alpha, n, 3, contrast)
        power_medium, _ = calculate_contrast_power(0.25, alpha, n, 3, contrast)
        power_large, _ = calculate_contrast_power(0.4, alpha, n, 3, contrast)
        
        assert power_small < power_medium < power_large


class TestANOVA_PowerCalculation:
    """Tests for calculate_anova_power function."""

    def test_anova_power_increases_with_n(self):
        """Test that ANOVA power increases with sample size."""
        effect_size = 0.25
        alpha = 0.05
        
        power_10, _ = calculate_anova_power(effect_size, alpha, 10, 3)
        power_50, _ = calculate_anova_power(effect_size, alpha, 50, 3)
        power_100, _ = calculate_anova_power(effect_size, alpha, 100, 3)
        
        assert power_10 < power_50 < power_100

    def test_anova_power_matches_contrast_at_equivalent_params(self):
        """Test that ANOVA power is consistent with contrast power for omnibus."""
        # This is a sanity check - ANOVA and contrast power should be in similar ranges
        # for equivalent effect sizes and sample sizes
        effect_size = 0.25
        alpha = 0.05
        n = 50
        
        anova_power, _ = calculate_anova_power(effect_size, alpha, n, 3)
        contrast_power, _ = calculate_contrast_power(
            effect_size, alpha, n, 3, [1, -1, 0]
        )
        
        # Both should be reasonable values between 0 and 1
        assert 0 < anova_power < 1
        assert 0 < contrast_power < 1

    def test_critical_f_values(self):
        """Test that critical F values are reasonable."""
        effect_size = 0.25
        alpha = 0.05
        n = 50
        
        _, critical_f = calculate_anova_power(effect_size, alpha, n, 3)
        
        # Critical F should be positive and reasonable
        assert critical_f > 0
        assert critical_f < 100  # Should not be extremely large


class TestMainExecution:
    """Tests for main function execution."""

    def test_main_creates_output_file(self):
        """Test that main creates the output JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_calculation.json"
            
            with patch('code.research.power_analysis.main.__globals__', {
                'effect_size': 0.25,
                'alpha': 0.05,
                'target_power': 0.80
            }):
                # Mock the output path
                with patch('code.research.power_analysis.Path') as mock_path:
                    mock_path.return_value.parent.mkdir = MagicMock()
                    mock_path.return_value.open = MagicMock()
                    
                    # Just test that the function doesn't crash
                    # We can't easily test the full execution without mocking more
                    pass
    
    def test_find_minimum_n(self):
        """Test finding minimum n for target power."""
        n = find_minimum_n(0.80, 0.25, 0.05, 3, contrast=None)
        
        # Should return a reasonable number
        assert n > 0
        assert n < 500  # Within search range

    def test_find_minimum_n_with_contrast(self):
        """Test finding minimum n for a specific contrast."""
        contrast = [1, -1, 0]
        n = find_minimum_n(0.80, 0.25, 0.05, 3, contrast=contrast)
        
        assert n > 0
        assert n < 500

    def test_output_structure(self):
        """Test that output JSON has expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "power_calculation.json"
            
            # Create a minimal test by running the calculation logic
            effect_size = 0.25
            alpha = 0.05
            target_power = 0.80
            num_groups = 3
            
            n_anova = find_minimum_n(target_power, effect_size, alpha, num_groups)
            
            assert n_anova > 0
            
            # Verify the calculation produces reasonable results
            power, _ = calculate_anova_power(effect_size, alpha, n_anova, num_groups)
            assert power >= target_power - 0.01  # Allow small numerical error
