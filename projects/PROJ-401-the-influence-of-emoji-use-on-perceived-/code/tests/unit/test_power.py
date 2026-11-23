import os
import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml
import numpy as np

from src.analysis.power import (
    calculate_min_sample_size,
    run_power_analysis,
    save_power_analysis,
    main
)


class TestCalculateMinSampleSize:
    """Unit tests for the calculate_min_sample_size function."""

    def test_calculate_min_sample_size_basic(self):
        """Test basic calculation with standard parameters."""
        # Cohen's f² = 0.02 (small effect), power = 0.80, alpha = 0.05
        # Approximate formula: N ≈ (L / f²) + k + 1
        # where L is the non-centrality parameter for the desired power
        # For power=0.80, alpha=0.05, L is approximately 7.85 (for F-test)
        # k is the number of predictors (excluding intercept)
        effect_size = 0.02
        power = 0.80
        alpha = 0.05
        num_predictors = 3  # text_length, punctuation_count, emoji_present

        result = calculate_min_sample_size(effect_size, power, alpha, num_predictors)

        assert isinstance(result, int)
        assert result > 0
        # With small effect size, N should be relatively large (hundreds)
        assert result > 100

    def test_calculate_min_sample_size_large_effect(self):
        """Test calculation with large effect size."""
        effect_size = 0.35  # Large effect
        power = 0.80
        alpha = 0.05
        num_predictors = 2

        result = calculate_min_sample_size(effect_size, power, alpha, num_predictors)

        assert isinstance(result, int)
        assert result > 0
        # Large effect size requires smaller sample
        assert result < 100

    def test_calculate_min_sample_size_high_power(self):
        """Test calculation with higher power requirement."""
        effect_size = 0.02
        power = 0.90
        alpha = 0.05
        num_predictors = 3

        result_high = calculate_min_sample_size(effect_size, power, alpha, num_predictors)

        # Lower power
        power = 0.80
        result_low = calculate_min_sample_size(effect_size, power, alpha, num_predictors)

        # Higher power should require larger sample
        assert result_high > result_low

    def test_calculate_min_sample_size_multiple_predictors(self):
        """Test that more predictors increase required sample size."""
        effect_size = 0.02
        power = 0.80
        alpha = 0.05

        result_2 = calculate_min_sample_size(effect_size, power, alpha, 2)
        result_5 = calculate_min_sample_size(effect_size, power, alpha, 5)

        assert result_5 > result_2


class TestRunPowerAnalysis:
    """Unit tests for the run_power_analysis function."""

    def test_run_power_analysis_returns_dict(self):
        """Test that run_power_analysis returns a dictionary with required keys."""
        effect_size = 0.02
        power = 0.80
        alpha = 0.05
        num_predictors = 3

        result = run_power_analysis(effect_size, power, alpha, num_predictors)

        assert isinstance(result, dict)
        assert 'required_sample_size' in result
        assert 'effect_size' in result
        assert 'power' in result
        assert 'alpha' in result
        assert 'num_predictors' in result
        assert 'description' in result

    def test_run_power_analysis_values_match_input(self):
        """Test that returned values match the input parameters."""
        effect_size = 0.05
        power = 0.85
        alpha = 0.01
        num_predictors = 4

        result = run_power_analysis(effect_size, power, alpha, num_predictors)

        assert result['effect_size'] == effect_size
        assert result['power'] == power
        assert result['alpha'] == alpha
        assert result['num_predictors'] == num_predictors

    def test_run_power_analysis_sample_size_positive(self):
        """Test that the calculated sample size is positive."""
        effect_size = 0.02
        power = 0.80
        alpha = 0.05
        num_predictors = 3

        result = run_power_analysis(effect_size, power, alpha, num_predictors)

        assert result['required_sample_size'] > 0


class TestSavePowerAnalysis:
    """Unit tests for the save_power_analysis function."""

    def test_save_power_analysis_creates_file(self):
        """Test that save_power_analysis creates the output file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "power_analysis.yaml"
            analysis_result = {
                'required_sample_size': 500,
                'effect_size': 0.02,
                'power': 0.80,
                'alpha': 0.05,
                'num_predictors': 3,
                'description': 'Test power analysis'
            }

            save_power_analysis(analysis_result, output_path)

            assert output_path.exists()

    def test_save_power_analysis_content(self):
        """Test that the saved file contains valid YAML with correct content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "power_analysis.yaml"
            expected_result = {
                'required_sample_size': 600,
                'effect_size': 0.02,
                'power': 0.80,
                'alpha': 0.05,
                'num_predictors': 3,
                'description': 'MVP power analysis for emoji intensity study'
            }

            save_power_analysis(expected_result, output_path)

            with open(output_path, 'r') as f:
                saved_data = yaml.safe_load(f)

            assert saved_data['required_sample_size'] == expected_result['required_sample_size']
            assert saved_data['effect_size'] == expected_result['effect_size']
            assert saved_data['power'] == expected_result['power']
            assert saved_data['alpha'] == expected_result['alpha']
            assert saved_data['num_predictors'] == expected_result['num_predictors']

    def test_save_power_analysis_creates_directory(self):
        """Test that save_power_analysis creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "state" / "subdir" / "power_analysis.yaml"

            analysis_result = {
                'required_sample_size': 500,
                'effect_size': 0.02,
                'power': 0.80,
                'alpha': 0.05,
                'num_predictors': 3,
                'description': 'Test'
            }

            save_power_analysis(analysis_result, output_path)

            assert output_path.exists()


class TestMain:
    """Unit tests for the main function entry point."""

    @patch('src.analysis.power.calculate_min_sample_size')
    @patch('src.analysis.power.save_power_analysis')
    @patch('src.analysis.power.Path')
    def test_main_executes_full_pipeline(self, mock_path, mock_save, mock_calc):
        """Test that main orchestrates the full power analysis pipeline."""
        mock_calc.return_value = 500
        mock_path.return_value = Path("/fake/path")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "state" / "power_analysis.yaml"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Mock the Path constructor to return our real temp path
            mock_path.return_value = output_path

            # Run main
            main(output_path=str(output_path))

            # Verify calculate_min_sample_size was called
            mock_calc.assert_called_once()
            # Verify save_power_analysis was called
            mock_save.assert_called_once()

    def test_main_with_real_path(self):
        """Test main function with a real temporary file path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "power_analysis.yaml"

            # This should run without errors and create the file
            main(output_path=str(output_path))

            assert output_path.exists()

            # Verify content
            with open(output_path, 'r') as f:
                data = yaml.safe_load(f)

            assert 'required_sample_size' in data
            assert data['required_sample_size'] > 0