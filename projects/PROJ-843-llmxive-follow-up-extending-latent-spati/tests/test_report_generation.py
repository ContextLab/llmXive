"""
Unit tests for code/eval/report.py (Task T021).

These tests verify the hypothesis verification report generation logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.report import (
    load_metrics_report,
    calculate_inference_time_reduction,
    check_threshold_pass,
    format_world_score_comparison,
    format_anova_results,
    format_sensitivity_analysis,
    generate_hypothesis_verification_report
)

from config import get_results_dir


class TestLoadMetricsReport:
    """Tests for load_metrics_report function."""
    
    def test_load_valid_metrics(self, tmp_path):
        """Test loading a valid metrics JSON file."""
        metrics_data = {
            "dense": {"inference_time_seconds": 100.0, "world_score": 0.85},
            "sparse": {"inference_time_seconds": 50.0, "sparse_consistency_score": 0.82},
            "generated_at": "2024-01-01"
        }
        
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        result = load_metrics_report(metrics_file)
        assert result == metrics_data
        assert result["dense"]["inference_time_seconds"] == 100.0
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.json"
        
        with pytest.raises(FileNotFoundError):
            load_metrics_report(non_existent)
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises JSONDecodeError."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            load_metrics_report(invalid_file)


class TestCalculateInferenceTimeReduction:
    """Tests for calculate_inference_time_reduction function."""
    
    def test_normal_reduction(self):
        """Test calculation with valid data."""
        metrics = {
            "dense": {"inference_time_seconds": 100.0},
            "sparse": {"inference_time_seconds": 60.0}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        # (100 - 60) / 100 * 100 = 40%
        assert reduction == 40.0
    
    def test_high_reduction(self):
        """Test calculation with high reduction."""
        metrics = {
            "dense": {"inference_time_seconds": 200.0},
            "sparse": {"inference_time_seconds": 50.0}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        # (200 - 50) / 200 * 100 = 75%
        assert reduction == 75.0
    
    def test_no_reduction(self):
        """Test calculation when sparse is slower."""
        metrics = {
            "dense": {"inference_time_seconds": 100.0},
            "sparse": {"inference_time_seconds": 120.0}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        # (100 - 120) / 100 * 100 = -20%
        assert reduction == -20.0
    
    def test_missing_dense_time(self):
        """Test handling of missing dense time."""
        metrics = {
            "dense": {},
            "sparse": {"inference_time_seconds": 60.0}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        assert reduction is None
    
    def test_missing_sparse_time(self):
        """Test handling of missing sparse time."""
        metrics = {
            "dense": {"inference_time_seconds": 100.0},
            "sparse": {}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        assert reduction is None
    
    def test_zero_dense_time(self):
        """Test handling of zero dense time (division by zero)."""
        metrics = {
            "dense": {"inference_time_seconds": 0.0},
            "sparse": {"inference_time_seconds": 50.0}
        }
        
        reduction = calculate_inference_time_reduction(metrics)
        assert reduction is None


class TestCheckThresholdPass:
    """Tests for check_threshold_pass function."""
    
    def test_passes_threshold(self):
        """Test when reduction meets threshold."""
        assert check_threshold_pass(40.0, 40.0) is True
        assert check_threshold_pass(50.0, 40.0) is True
        assert check_threshold_pass(40.1, 40.0) is True
    
    def test_fails_threshold(self):
        """Test when reduction is below threshold."""
        assert check_threshold_pass(39.9, 40.0) is False
        assert check_threshold_pass(30.0, 40.0) is False
        assert check_threshold_pass(-10.0, 40.0) is False
    
    def test_none_reduction(self):
        """Test when reduction is None."""
        assert check_threshold_pass(None, 40.0) is False
    
    def test_custom_threshold(self):
        """Test with custom threshold."""
        assert check_threshold_pass(50.0, 50.0) is True
        assert check_threshold_pass(49.9, 50.0) is False


class TestFormatWorldScoreComparison:
    """Tests for format_world_score_comparison function."""
    
    def test_all_metrics_present(self):
        """Test formatting when all metrics are present."""
        metrics = {
            "dense": {"world_score": 0.85},
            "sparse": {"sparse_consistency_score": 0.82, "fid": 12.5}
        }
        
        result = format_world_score_comparison(metrics)
        assert "WorldScore (Dense Baseline): 0.8500" in result
        assert "Sparse-Consistency Score: 0.8200" in result
        assert "Fréchet Inception Distance (FID): 12.5000" in result
    
    def test_missing_metrics(self):
        """Test formatting when some metrics are missing."""
        metrics = {
            "dense": {},
            "sparse": {}
        }
        
        result = format_world_score_comparison(metrics)
        assert "Not available" in result


class TestFormatAnovaResults:
    """Tests for format_anova_results function."""
    
    def test_significant_interaction(self):
        """Test formatting with significant interaction effect."""
        metrics = {
            "anova": {"interaction_p_value": 0.01}
        }
        
        result = format_anova_results(metrics)
        assert "0.010000" in result
        assert "Significant interaction effect detected" in result
    
    def test_non_significant_interaction(self):
        """Test formatting with non-significant interaction effect."""
        metrics = {
            "anova": {"interaction_p_value": 0.15}
        }
        
        result = format_anova_results(metrics)
        assert "0.150000" in result
        assert "No significant interaction effect" in result
    
    def test_missing_anova(self):
        """Test formatting when anova results are missing."""
        metrics = {}
        
        result = format_anova_results(metrics)
        assert "not available" in result.lower()


class TestGenerateHypothesisVerificationReport:
    """Tests for generate_hypothesis_verification_report function."""
    
    def test_report_generation(self, tmp_path):
        """Test full report generation."""
        metrics_data = {
            "dense": {"inference_time_seconds": 100.0, "world_score": 0.85},
            "sparse": {
                "inference_time_seconds": 50.0,
                "sparse_consistency_score": 0.82,
                "fid": 15.0
            },
            "anova": {"interaction_p_value": 0.03},
            "sensitivity": {"world_score_stability": 0.02},
            "generated_at": "2024-01-01T00:00:00"
        }
        
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        output_file = tmp_path / "report.md"
        
        generate_hypothesis_verification_report(metrics_file, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Verify key sections exist
        assert "Hypothesis Verification Report" in content
        assert "Executive Summary" in content
        assert "Inference Time Reduction" in content
        assert "PASS" in content  # 50% > 40%
        assert "WorldScore" in content
        assert "ANOVA" in content
        assert "Sensitivity Analysis" in content
    
    def test_report_generation_fail(self, tmp_path):
        """Test report generation when threshold is not met."""
        metrics_data = {
            "dense": {"inference_time_seconds": 100.0},
            "sparse": {"inference_time_seconds": 80.0},  # Only 20% reduction
            "generated_at": "2024-01-01T00:00:00"
        }
        
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        output_file = tmp_path / "report.md"
        
        generate_hypothesis_verification_report(metrics_file, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = f.read()
        
        assert "FAIL" in content
        assert "20.00%" in content