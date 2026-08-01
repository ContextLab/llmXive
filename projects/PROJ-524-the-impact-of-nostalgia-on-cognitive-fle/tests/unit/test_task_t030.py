"""
Unit tests for code/task_t030_final_report.py.
Tests final report compilation and stability metrics.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t030_final_report import (
    calculate_stability_metrics,
    generate_sensitivity_summary,
    compile_final_report
)


class TestCalculateStabilityMetrics:
    def test_calculate_stability_metrics_all_significant(self):
        """Test stability when all thresholds yield significant results."""
        results = [
            {'threshold': 0.01, 'is_significant': True},
            {'threshold': 0.05, 'is_significant': True},
            {'threshold': 0.10, 'is_significant': True}
        ]

        metrics = calculate_stability_metrics(results)

        assert metrics['stable_count'] == 3
        assert metrics['unstable_count'] == 0
        assert metrics['stability_ratio'] == 1.0

    def test_calculate_stability_metrics_mixed(self):
        """Test stability with mixed results."""
        results = [
            {'threshold': 0.01, 'is_significant': False},
            {'threshold': 0.05, 'is_significant': True},
            {'threshold': 0.10, 'is_significant': True}
        ]

        metrics = calculate_stability_metrics(results)

        assert metrics['stable_count'] == 2
        assert metrics['unstable_count'] == 1
        assert metrics['stability_ratio'] == 2/3

    def test_calculate_stability_metrics_empty(self):
        """Test stability with empty results."""
        results = []

        metrics = calculate_stability_metrics(results)

        assert metrics['stable_count'] == 0
        assert metrics['unstable_count'] == 0
        assert metrics['stability_ratio'] == 0.0

class TestGenerateSensitivitySummary:
    def test_generate_sensitivity_summary(self):
        """Test sensitivity summary generation."""
        sensitivity_results = [
            {'threshold': 0.01, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.05, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.10, 'is_significant': False, 'p_value': 0.15}
        ]

        summary = generate_sensitivity_summary(sensitivity_results)

        assert 'thresholds_tested' in summary
        assert 'stability_assessment' in summary
        assert 'recommendation' in summary

    def test_generate_sensitivity_summary_borderline(self):
        """Test sensitivity summary with borderline results."""
        sensitivity_results = [
            {'threshold': 0.04, 'is_significant': False, 'p_value': 0.049},
            {'threshold': 0.05, 'is_significant': True, 'p_value': 0.049},
            {'threshold': 0.06, 'is_significant': True, 'p_value': 0.049}
        ]

        summary = generate_sensitivity_summary(sensitivity_results)

        assert 'borderline' in summary['stability_assessment'].lower()

class TestCompileFinalReport:
    def test_compile_final_report(self):
        """Test final report compilation."""
        statistical_results = {
            'p_value': 0.03,
            'effect_size': 0.5,
            'power': 0.85
        }

        sensitivity_results = {
            'thresholds_tested': 3,
            'stability_assessment': 'stable'
        }

        report = compile_final_report(statistical_results, sensitivity_results)

        assert 'statistical_findings' in report
        assert 'sensitivity_analysis' in report
        assert 'conclusion' in report

    def test_compile_final_report_with_power(self):
        """Test final report with power analysis."""
        statistical_results = {
            'p_value': 0.03,
            'effect_size': 0.5,
            'power': 0.85,
            'mdes': 0.3
        }

        sensitivity_results = {
            'thresholds_tested': 3,
            'stability_assessment': 'stable'
        }

        report = compile_final_report(statistical_results, sensitivity_results)

        assert report['statistical_findings']['power'] == 0.85
        assert report['statistical_findings']['mdes'] == 0.3
