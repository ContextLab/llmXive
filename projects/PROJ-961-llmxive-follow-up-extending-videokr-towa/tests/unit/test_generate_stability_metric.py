"""
Unit tests for generate_stability_metric.py

Tests the robustness calculation logic for sensitivity analysis results.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.generate_stability_metric import (
    calculate_robustness,
    load_sensitivity_results,
    save_stability_metric
)
from utils.config import get_project_root, get_path, ensure_dir


class TestCalculateRobustness:
    """Tests for calculate_robustness function."""

    def test_all_significant(self):
        """Test when all thresholds are significant."""
        results = [
            {'threshold': 2, 'p_value': 0.01},
            {'threshold': 3, 'p_value': 0.02},
            {'threshold': 4, 'p_value': 0.03}
        ]
        metric = calculate_robustness(results)

        assert metric['significant_count'] == 3
        assert metric['total_thresholds'] == 3
        assert metric['robustness_status'] == 'PASS'
        assert metric['alpha'] == 0.05

    def test_two_significant(self):
        """Test when exactly 2 thresholds are significant (boundary case for PASS)."""
        results = [
            {'threshold': 2, 'p_value': 0.01},
            {'threshold': 3, 'p_value': 0.04},
            {'threshold': 4, 'p_value': 0.06}
        ]
        metric = calculate_robustness(results)

        assert metric['significant_count'] == 2
        assert metric['total_thresholds'] == 3
        assert metric['robustness_status'] == 'PASS'

    def test_one_significant(self):
        """Test when only 1 threshold is significant (should FAIL)."""
        results = [
            {'threshold': 2, 'p_value': 0.01},
            {'threshold': 3, 'p_value': 0.06},
            {'threshold': 4, 'p_value': 0.08}
        ]
        metric = calculate_robustness(results)

        assert metric['significant_count'] == 1
        assert metric['total_thresholds'] == 3
        assert metric['robustness_status'] == 'FAIL'

    def test_none_significant(self):
        """Test when no thresholds are significant."""
        results = [
            {'threshold': 2, 'p_value': 0.10},
            {'threshold': 3, 'p_value': 0.20},
            {'threshold': 4, 'p_value': 0.30}
        ]
        metric = calculate_robustness(results)

        assert metric['significant_count'] == 0
        assert metric['total_thresholds'] == 3
        assert metric['robustness_status'] == 'FAIL'

    def test_missing_p_value(self):
        """Test handling of missing p_value (should skip)."""
        results = [
            {'threshold': 2, 'p_value': 0.01},
            {'threshold': 3},  # Missing p_value
            {'threshold': 4, 'p_value': 0.06}
        ]
        metric = calculate_robustness(results)

        assert metric['significant_count'] == 1
        assert metric['total_thresholds'] == 3
        assert metric['robustness_status'] == 'FAIL'

    def test_custom_alpha(self):
        """Test with custom alpha threshold."""
        results = [
            {'threshold': 2, 'p_value': 0.06},
            {'threshold': 3, 'p_value': 0.07},
            {'threshold': 4, 'p_value': 0.08}
        ]
        # With alpha=0.10, all should be significant
        metric = calculate_robustness(results, alpha=0.10)

        assert metric['significant_count'] == 3
        assert metric['robustness_status'] == 'PASS'
        assert metric['alpha'] == 0.10

class TestLoadSensitivityResults:
    """Tests for load_sensitivity_results function."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        test_data = [{'threshold': 2, 'p_value': 0.01}]
        json_file = tmp_path / 'test_results.json'
        json_file.write_text(json.dumps(test_data))

        results = load_sensitivity_results(json_file)

        assert results == test_data

    def test_load_empty_json(self, tmp_path):
        """Test loading an empty JSON list."""
        json_file = tmp_path / 'empty_results.json'
        json_file.write_text('[]')

        results = load_sensitivity_results(json_file)

        assert results == []

    def test_load_invalid_file(self, tmp_path):
        """Test loading a non-existent file."""
        non_existent = tmp_path / 'non_existent.json'

        with pytest.raises(FileNotFoundError):
            load_sensitivity_results(non_existent)

class TestSaveStabilityMetric:
    """Tests for save_stability_metric function."""

    def test_save_metric(self, tmp_path):
        """Test saving a metric to JSON."""
        metric = {
            'significant_count': 2,
            'total_thresholds': 3,
            'alpha': 0.05,
            'robustness_status': 'PASS'
        }
        output_file = tmp_path / 'stability_metric.json'

        save_stability_metric(metric, output_file)

        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data == metric

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates parent directories if needed."""
        metric = {'test': 'data'}
        output_file = tmp_path / 'subdir' / 'nested' / 'metric.json'

        save_stability_metric(metric, output_file)

        assert output_file.exists()

class TestIntegration:
    """Integration tests for the full flow."""

    def test_full_flow(self, tmp_path):
        """Test the complete flow from input to output."""
        # Create input data
        input_data = [
            {'threshold': 2, 'p_value': 0.01},
            {'threshold': 3, 'p_value': 0.04},
            {'threshold': 4, 'p_value': 0.06}
        ]
        input_file = tmp_path / 'sensitivity_results.json'
        input_file.write_text(json.dumps(input_data))

        output_file = tmp_path / 'stability_metric.json'

        # Run the logic
        results = load_sensitivity_results(input_file)
        metric = calculate_robustness(results)
        save_stability_metric(metric, output_file)

        # Verify output
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_metric = json.load(f)

        assert saved_metric['significant_count'] == 2
        assert saved_metric['robustness_status'] == 'PASS'
        assert saved_metric['total_thresholds'] == 3