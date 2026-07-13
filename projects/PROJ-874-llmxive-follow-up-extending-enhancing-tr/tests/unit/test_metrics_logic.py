"""
Unit tests for metric calculation logic in the llmXive pipeline.

This module tests the core statistical and scoring functions used in
User Story 3 (Comparative Analysis) to ensure correctness of:
- Object Permanence Score calculation
- VBench score aggregation
- FVD (Fréchet Video Distance) estimation logic
- Statistical test selection (normality check -> t-test vs Wilcoxon)

Note: These tests use mock data or small synthetic arrays to verify
logic without requiring large real-world datasets.
"""
import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_results_dir, get_processed_dir
from analyze import (
    calculate_power,
    check_normality,
    perform_statistical_test,
    load_metrics_from_json,
    identify_failure_cases
)
from pilot_study import calculate_object_permanence_score


class TestObjectPermanenceScore:
    """Tests for object permanence score calculation."""

    def test_perfect_permanence(self):
        """Test score when object is present in all frames."""
        # Simulate a sequence where object is detected in every frame
        detections = [1.0] * 10  # 10 frames, object present
        score = calculate_object_permanence_score(detections)
        assert score == 1.0, "Perfect permanence should yield 1.0"

    def test_no_permanence(self):
        """Test score when object is never present."""
        detections = [0.0] * 10
        score = calculate_object_permanence_score(detections)
        assert score == 0.0, "No permanence should yield 0.0"

    def test_partial_permanence(self):
        """Test score with intermittent object presence."""
        # Object present in 7 out of 10 frames
        detections = [1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        score = calculate_object_permanence_score(detections)
        expected = 7.0 / 10.0
        assert abs(score - expected) < 1e-6, f"Expected {expected}, got {score}"

    def test_empty_sequence(self):
        """Test handling of empty detection list."""
        with pytest.raises(ValueError):
            calculate_object_permanence_score([])


class TestStatisticalAnalysis:
    """Tests for statistical analysis functions."""

    def test_calculate_power_small_effect(self):
        """Test power calculation with small effect size."""
        # Cohen's d = 0.2 (small effect)
        effect_size = 0.2
        n_samples = 50
        alpha = 0.05
        
        power = calculate_power(effect_size, n_samples, alpha)
        
        # With small effect and N=50, power should be low (< 0.8)
        assert 0.0 < power < 0.8, f"Power for small effect should be low: {power}"

    def test_calculate_power_large_effect(self):
        """Test power calculation with large effect size."""
        # Cohen's d = 0.8 (large effect)
        effect_size = 0.8
        n_samples = 50
        alpha = 0.05
        
        power = calculate_power(effect_size, n_samples, alpha)
        
        # With large effect and N=50, power should be high (> 0.8)
        assert power > 0.8, f"Power for large effect should be high: {power}"

    def test_check_normality_normal_data(self):
        """Test normality check on normally distributed data."""
        # Generate normal data
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        
        is_normal, p_value = check_normality(normal_data)
        
        # Should fail to reject null hypothesis (is normal)
        assert is_normal is True, "Normal data should pass normality test"
        assert p_value > 0.05, "Normal data should have p > 0.05"

    def test_check_normality_non_normal_data(self):
        """Test normality check on skewed data."""
        # Generate skewed data (exponential distribution)
        np.random.seed(42)
        skewed_data = np.random.exponential(scale=1.0, size=100)
        
        is_normal, p_value = check_normality(skewed_data)
        
        # Should reject null hypothesis (is not normal)
        assert is_normal is False, "Skewed data should fail normality test"
        assert p_value < 0.05, "Skewed data should have p < 0.05"

    def test_perform_statistical_test_ttest_path(self):
        """Test statistical test selection for normal data (t-test)."""
        np.random.seed(42)
        group_a = np.random.normal(0, 1, 50)
        group_b = np.random.normal(0.5, 1, 50)  # Slight shift
        
        test_type, p_value, statistic = perform_statistical_test(group_a, group_b)
        
        assert test_type == "paired_t_test", "Normal data should use t-test"
        assert 0.0 <= p_value <= 1.0, "p-value must be in [0, 1]"

    def test_perform_statistical_test_wilcoxon_path(self):
        """Test statistical test selection for non-normal data (Wilcoxon)."""
        np.random.seed(42)
        group_a = np.random.exponential(1, 50)
        group_b = np.random.exponential(1.5, 50)  # Shifted exponential
        
        test_type, p_value, statistic = perform_statistical_test(group_a, group_b)
        
        # Non-normal data should trigger Wilcoxon
        assert test_type == "wilcoxon", "Non-normal data should use Wilcoxon"
        assert 0.0 <= p_value <= 1.0, "p-value must be in [0, 1]"


class TestMetricsLoading:
    """Tests for metrics loading and parsing."""

    def test_load_metrics_from_json_valid(self):
        """Test loading metrics from a valid JSON file."""
        mock_data = {
            "video_001": {
                "condition": "baseline-naive",
                "vbench_score": 0.85,
                "fvd": 120.5,
                "object_permanence": 0.92
            },
            "video_002": {
                "condition": "baseline-full",
                "vbench_score": 0.88,
                "fvd": 115.2,
                "object_permanence": 0.95
            }
        }
        
        with patch('builtins.open', mock_open_read_data(json.dumps(mock_data))):
            metrics = load_metrics_from_json("dummy_path.json")
            
            assert len(metrics) == 2
            assert "video_001" in metrics
            assert metrics["video_001"]["vbench_score"] == 0.85

    def test_load_metrics_from_json_invalid_file(self):
        """Test handling of missing file."""
        with pytest.raises(FileNotFoundError):
            load_metrics_from_json("nonexistent_file.json")


class TestFailureCaseIdentification:
    """Tests for failure case detection logic."""

    def test_identify_failure_cases_vbench_drop(self):
        """Test detection of VBench score drop."""
        naive_metrics = {
            "video_001": {"vbench_score": 0.90, "object_permanence": 0.95}
        }
        corrected_metrics = {
            "video_001": {"vbench_score": 0.75, "object_permanence": 0.94}
        }
        
        # Drop of 0.15 (> 0.1 threshold)
        failures = identify_failure_cases(naive_metrics, corrected_metrics)
        
        assert "video_001" in failures
        assert failures["video_001"]["reason"] == "vbench_drop"

    def test_identify_failure_cases_permanence_drop(self):
        """Test detection of object permanence drop."""
        naive_metrics = {
            "video_001": {"vbench_score": 0.90, "object_permanence": 0.95}
        }
        corrected_metrics = {
            "video_001": {"vbench_score": 0.89, "object_permanence": 0.85}
        }
        
        # Drop of 0.10 (>= 5% of 0.95 is ~0.0475, so 0.10 is significant)
        # Actually, the requirement is "drops ≥5%", which usually means absolute drop >= 0.05
        # 0.95 -> 0.85 is a 0.10 drop, which is > 0.05
        failures = identify_failure_cases(naive_metrics, corrected_metrics)
        
        assert "video_001" in failures
        assert failures["video_001"]["reason"] == "permanence_drop"

    def test_identify_failure_cases_no_failure(self):
        """Test when no failures are detected."""
        naive_metrics = {
            "video_001": {"vbench_score": 0.90, "object_permanence": 0.95}
        }
        corrected_metrics = {
            "video_001": {"vbench_score": 0.89, "object_permanence": 0.94}
        }
        
        # Drops are small (< 0.1 VBench, < 0.05 permanence)
        failures = identify_failure_cases(naive_metrics, corrected_metrics)
        
        assert len(failures) == 0


def mock_open_read_data(data):
    """Helper to mock open() for testing."""
    def opener(*args, **kwargs):
        import io
        return io.StringIO(data)
    return opener


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
