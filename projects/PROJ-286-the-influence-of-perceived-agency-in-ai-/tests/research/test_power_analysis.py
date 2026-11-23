"""
Unit tests for the power analysis module (T002).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path if running from tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.research.power_analysis import (
    normalize_contrast,
    calculate_contrast_power,
    calculate_anova_power,
    find_minimum_n,
    main
)


class TestNormalizeContrast:
    def test_normalize_valid_contrast(self):
        """Test normalization of a standard contrast vector."""
        contrast = [1, -1, 0]
        normalized = normalize_contrast(contrast)
        # Sum of squares should be 1
        assert np.isclose(sum(c**2 for c in normalized), 1.0)
        # Direction should be preserved
        assert normalized[0] > 0
        assert normalized[1] < 0

    def test_normalize_zeros(self):
        """Test that zero vector raises error."""
        with pytest.raises(ValueError):
            normalize_contrast([0, 0, 0])


class TestContrastPowerCalculation:
    def test_calculate_contrast_power_basic(self):
        """Test basic t-test power calculation."""
        n_per_group, total_n = calculate_contrast_power(
            effect_size_d=0.5,
            alpha=0.05,
            power_target=0.80,
            n_groups=3
        )
        assert n_per_group > 0
        assert total_n > 0
        assert total_n == int(np.ceil(n_per_group * 2))

    def test_calculate_contrast_power_large_effect(self):
        """Test with large effect size -> smaller N."""
        n_small, _ = calculate_contrast_power(0.8, 0.05, 0.80, 3)
        n_large, _ = calculate_contrast_power(0.2, 0.05, 0.80, 3)
        assert n_small < n_large


class TestANOVA_PowerCalculation:
    def test_calculate_anova_power_basic(self):
        """Test basic ANOVA power calculation."""
        n_per_group, total_n = calculate_anova_power(
            effect_size_f=0.25,
            alpha=0.05,
            power_target=0.80,
            n_groups=3
        )
        assert n_per_group > 0
        assert total_n > 0
        assert total_n == int(np.ceil(n_per_group * 3))

    def test_calculate_anova_power_small_effect(self):
        """Test with small effect size -> larger N."""
        n_small, _ = calculate_anova_power(0.1, 0.05, 0.80, 3)
        n_large, _ = calculate_anova_power(0.5, 0.05, 0.80, 3)
        assert n_small > n_large


class TestMinimumN:
    def test_find_minimum_n(self):
        """Test that max is selected."""
        assert find_minimum_n(30, 50) == 50
        assert find_minimum_n(60, 40) == 60


class TestMainExecution:
    def test_main_creates_file(self):
        """Test that main() creates the expected output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the output path
            with patch('code.research.power_analysis.PROJECT_ROOT', Path(tmpdir)):
                with patch('code.research.power_analysis.sys.exit', return_value=0):
                    result = main()
            
            output_path = Path(tmpdir) / "research" / "power_calculation.json"
            assert output_path.exists()
            
            with open(output_path) as f:
                data = json.load(f)
            
            assert "params" in data
            assert "results" in data
            assert "total_n" in data["results"]
            assert data["status"] == "success"

    def test_main_parameters(self):
        """Verify the hard-coded parameters are used correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('code.research.power_analysis.PROJECT_ROOT', Path(tmpdir)):
                with patch('code.research.power_analysis.sys.exit', return_value=0):
                    main()
            
            output_path = Path(tmpdir) / "research" / "power_calculation.json"
            with open(output_path) as f:
                data = json.load(f)
            
            params = data["params"]
            assert params["effect_size_f"] == 0.25
            assert params["alpha"] == 0.05
            assert params["target_power"] == 0.80
            assert params["groups"] == 3
            assert params["effect_size_d_contrast"] == 0.50