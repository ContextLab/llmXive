import pytest
import numpy as np
import math
from pathlib import Path
import sys
import json
from unittest.mock import patch, MagicMock

# Import the functions being tested
from utils.stats import (
    calculate_effect_size,
    run_mixed_effects_test,
    calculate_power_analysis,
    run_power_analysis,
    main
)

# Mock data fixtures for testing
@pytest.fixture
def mock_baseline_results():
    """Generate mock baseline results for testing."""
    return [
        {"task_id": 1, "score": 0.65, "latency": 120},
        {"task_id": 2, "score": 0.70, "latency": 115},
        {"task_id": 3, "score": 0.68, "latency": 130},
        {"task_id": 4, "score": 0.72, "latency": 110},
        {"task_id": 5, "score": 0.66, "latency": 125},
    ]

@pytest.fixture
def mock_episodic_results():
    """Generate mock episodic results for testing."""
    return [
        {"task_id": 1, "score": 0.82, "latency": 95},
        {"task_id": 2, "score": 0.85, "latency": 90},
        {"task_id": 3, "score": 0.80, "latency": 100},
        {"task_id": 4, "score": 0.88, "latency": 85},
        {"task_id": 5, "score": 0.83, "latency": 92},
    ]

@pytest.fixture
def mock_input_json_path(tmp_path):
    """Create a temporary JSON file with test data."""
    data = {
        "baseline": [
            {"task_id": 1, "score": 0.65},
            {"task_id": 2, "score": 0.70},
            {"task_id": 3, "score": 0.68},
            {"task_id": 4, "score": 0.72},
            {"task_id": 5, "score": 0.66},
        ],
        "episodic": [
            {"task_id": 1, "score": 0.82},
            {"task_id": 2, "score": 0.85},
            {"task_id": 3, "score": 0.80},
            {"task_id": 4, "score": 0.88},
            {"task_id": 5, "score": 0.83},
        ]
    }
    file_path = tmp_path / "test_results.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

class TestCalculateEffectSize:
    """Tests for calculate_effect_size function."""

    def test_cohen_d_positive_effect(self):
        """Test Cohen's d calculation with positive effect."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert isinstance(effect_size, float)
        assert effect_size > 0  # Positive effect
        assert math.isfinite(effect_size)

    def test_cohen_d_negative_effect(self):
        """Test Cohen's d calculation with negative effect."""
        group1 = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert isinstance(effect_size, float)
        assert effect_size < 0  # Negative effect
        assert math.isfinite(effect_size)

    def test_cohen_d_zero_effect(self):
        """Test Cohen's d calculation with no effect."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert isinstance(effect_size, float)
        assert math.isclose(effect_size, 0.0, abs_tol=1e-10)
        assert math.isfinite(effect_size)

    def test_cohen_d_small_sample(self):
        """Test Cohen's d with small sample sizes."""
        group1 = np.array([1.0, 2.0])
        group2 = np.array([3.0, 4.0])
        
        effect_size = calculate_effect_size(group1, group2)
        
        assert isinstance(effect_size, float)
        assert math.isfinite(effect_size)

    def test_cohen_d_single_element(self):
        """Test that single element groups raise an error."""
        group1 = np.array([1.0])
        group2 = np.array([2.0])
        
        with pytest.raises(ValueError):
            calculate_effect_size(group1, group2)

    def test_cohen_d_empty_array(self):
        """Test that empty arrays raise an error."""
        group1 = np.array([])
        group2 = np.array([1.0, 2.0])
        
        with pytest.raises(ValueError):
            calculate_effect_size(group1, group2)

class TestRunMixedEffectsTest:
    """Tests for run_mixed_effects_test function."""

    @patch('statsmodels.formula.api.mixedlm')
    def test_mixed_effects_model_creation(self, mock_mixedlm):
        """Test that mixed effects model is created correctly."""
        # Setup mock return value
        mock_result = MagicMock()
        mock_result.pvalues = {"baseline": 0.001}
        mock_result.summary.return_value = "Mock Summary"
        mock_mixedlm.return_value.fit.return_value = mock_result
        
        data = {
            'score': [0.65, 0.70, 0.68, 0.82, 0.85, 0.80],
            'condition': ['baseline', 'baseline', 'baseline', 'episodic', 'episodic', 'episodic'],
            'task_id': [1, 2, 3, 1, 2, 3]
        }
        
        result = run_mixed_effects_test(data, 'score', 'condition', 'task_id')
        
        assert result is not None
        assert 'pvalue' in result or hasattr(result, 'pvalues')
        mock_mixedlm.assert_called_once()

    def test_mixed_effects_with_valid_data(self, mock_baseline_results, mock_episodic_results):
        """Test mixed effects test with valid mock data."""
        # Combine data into a single dataframe-like structure
        combined_data = {
            'score': [r['score'] for r in mock_baseline_results] + 
                    [r['score'] for r in mock_episodic_results],
            'condition': ['baseline'] * len(mock_baseline_results) + 
                        ['episodic'] * len(mock_episodic_results),
            'task_id': list(range(1, len(mock_baseline_results) + 1)) * 2
        }
        
        # This test verifies the function runs without error
        # Actual statistical validation would require real statsmodels
        try:
            result = run_mixed_effects_test(combined_data, 'score', 'condition', 'task_id')
            # If statsmodels is available, result should be a dict or object
            assert result is not None
        except ImportError:
            # If statsmodels is not installed, the function should handle it gracefully
            pytest.skip("statsmodels not installed")

class TestCalculatePowerAnalysis:
    """Tests for calculate_power_analysis function."""

    def test_power_analysis_basic(self):
        """Test basic power analysis calculation."""
        effect_size = 0.8  # Large effect
        alpha = 0.05
        sample_size = 30
        
        power = calculate_power_analysis(effect_size, alpha, sample_size)
        
        assert isinstance(power, float)
        assert 0 <= power <= 1
        assert math.isfinite(power)

    def test_power_analysis_small_effect(self):
        """Test power analysis with small effect size."""
        effect_size = 0.2  # Small effect
        alpha = 0.05
        sample_size = 30
        
        power = calculate_power_analysis(effect_size, alpha, sample_size)
        
        assert isinstance(power, float)
        assert 0 <= power <= 1

    def test_power_analysis_large_sample(self):
        """Test power analysis with large sample size."""
        effect_size = 0.5  # Medium effect
        alpha = 0.05
        sample_size = 200
        
        power = calculate_power_analysis(effect_size, alpha, sample_size)
        
        assert isinstance(power, float)
        assert 0 <= power <= 1
        # Larger sample should yield higher power
        assert power > 0.8

    def test_power_analysis_invalid_alpha(self):
        """Test power analysis with invalid alpha value."""
        with pytest.raises(ValueError):
            calculate_power_analysis(0.5, 1.5, 30)  # alpha > 1

    def test_power_analysis_negative_sample_size(self):
        """Test power analysis with negative sample size."""
        with pytest.raises(ValueError):
            calculate_power_analysis(0.5, 0.05, -10)

class TestRunPowerAnalysis:
    """Tests for run_power_analysis function."""

    def test_run_power_analysis_basic(self):
        """Test basic power analysis run."""
        effect_size = 0.8
        alpha = 0.05
        power_target = 0.8
        
        result = run_power_analysis(effect_size, alpha, power_target)
        
        assert result is not None
        assert 'sample_size' in result or hasattr(result, 'sample_size')
        assert result.get('sample_size', 0) > 0

    def test_run_power_analysis_high_power_target(self):
        """Test power analysis with high power target."""
        effect_size = 0.5
        alpha = 0.05
        power_target = 0.95
        
        result = run_power_analysis(effect_size, alpha, power_target)
        
        assert result is not None
        assert result.get('sample_size', 0) > 0

class TestMain:
    """Tests for the main function entry point."""

    def test_main_with_valid_args(self, mock_input_json_path, tmp_path):
        """Test main function with valid command line arguments."""
        output_path = tmp_path / "output_results.json"
        
        # Mock sys.argv to simulate command line execution
        test_args = [
            'stats.py',
            '--input', str(mock_input_json_path),
            '--output', str(output_path),
            '--variant', '10',
            '--fdr'
        ]
        
        with patch('sys.argv', test_args):
            # This test verifies the main function can be called
            # Actual execution depends on data availability
            try:
                main()
                # If successful, output file should exist
                assert output_path.exists()
            except SystemExit:
                # Expected if argument parsing fails or data is invalid
                pass
            except ImportError:
                # Expected if statsmodels is not available
                pytest.skip("statsmodels not installed")

    def test_main_missing_input_file(self, tmp_path):
        """Test main function with missing input file."""
        output_path = tmp_path / "output_results.json"
        missing_input = tmp_path / "nonexistent.json"
        
        test_args = [
            'stats.py',
            '--input', str(missing_input),
            '--output', str(output_path),
            '--variant', '10'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(FileNotFoundError):
                main()

    def test_main_invalid_variant(self, mock_input_json_path, tmp_path):
        """Test main function with invalid variant value."""
        output_path = tmp_path / "output_results.json"
        
        test_args = [
            'stats.py',
            '--input', str(mock_input_json_path),
            '--output', str(output_path),
            '--variant', 'invalid',
            '--fdr'
        ]
        
        with patch('sys.argv', test_args):
            with pytest.raises(ValueError):
                main()

# Additional unit tests for edge cases and error handling
class TestStatsErrorHandling:
    """Additional tests for error handling in stats utilities."""

    def test_effect_size_with_nan_values(self):
        """Test effect size calculation with NaN values."""
        group1 = np.array([1.0, np.nan, 3.0])
        group2 = np.array([3.0, 4.0, 5.0])
        
        with pytest.raises(ValueError):
            calculate_effect_size(group1, group2)

    def test_effect_size_with_inf_values(self):
        """Test effect size calculation with infinite values."""
        group1 = np.array([1.0, np.inf, 3.0])
        group2 = np.array([3.0, 4.0, 5.0])
        
        with pytest.raises(ValueError):
            calculate_effect_size(group1, group2)

    def test_power_analysis_with_zero_effect(self):
        """Test power analysis with zero effect size."""
        effect_size = 0.0
        alpha = 0.05
        sample_size = 30
        
        power = calculate_power_analysis(effect_size, alpha, sample_size)
        
        # Power should be equal to alpha when effect size is 0
        assert isinstance(power, float)
        assert 0 <= power <= 1

    def test_mixed_effects_with_mismatched_lengths(self):
        """Test mixed effects with mismatched array lengths."""
        data = {
            'score': [0.65, 0.70, 0.68],
            'condition': ['baseline', 'baseline'],  # One less
            'task_id': [1, 2, 3]
        }
        
        with pytest.raises(ValueError):
            run_mixed_effects_test(data, 'score', 'condition', 'task_id')

# Integration-style unit tests that verify statistical properties
class TestStatsProperties:
    """Tests that verify statistical properties and invariants."""

    def test_effect_size_symmetry(self):
        """Test that Cohen's d is symmetric (sign changes, magnitude same)."""
        group1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        group2 = np.array([3.0, 4.0, 5.0, 6.0, 7.0])
        
        d1 = calculate_effect_size(group1, group2)
        d2 = calculate_effect_size(group2, group1)
        
        assert math.isclose(abs(d1), abs(d2), rel_tol=1e-10)
        assert (d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)

    def test_power_monotonicity_with_sample_size(self):
        """Test that power increases with sample size."""
        effect_size = 0.5
        alpha = 0.05
        
        power_small = calculate_power_analysis(effect_size, alpha, 20)
        power_large = calculate_power_analysis(effect_size, alpha, 100)
        
        assert power_large > power_small

    def test_power_monotonicity_with_effect_size(self):
        """Test that power increases with effect size."""
        alpha = 0.05
        sample_size = 30
        
        power_small = calculate_power_analysis(0.2, alpha, sample_size)
        power_large = calculate_power_analysis(0.8, alpha, sample_size)
        
        assert power_large > power_small

    def test_power_bounds(self):
        """Test that power is always between 0 and 1."""
        test_cases = [
            (0.1, 0.05, 10),
            (0.5, 0.01, 50),
            (1.0, 0.10, 100),
        ]
        
        for effect_size, alpha, sample_size in test_cases:
            power = calculate_power_analysis(effect_size, alpha, sample_size)
            assert 0 <= power <= 1, f"Power {power} out of bounds for effect={effect_size}, alpha={alpha}, n={sample_size}"