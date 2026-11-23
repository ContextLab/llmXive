"""
Unit tests for code/task_t028_sensitivity_report.py.
Tests sensitivity report generation.
"""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t028_sensitivity_report import (
    generate_sensitivity_report
)


class TestGenerateSensitivityReport:
    def test_generate_sensitivity_report_basic(self):
        """Test basic sensitivity report generation."""
        sensitivity_results = [
            {'threshold': 0.01, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.05, 'is_significant': False, 'p_value': 0.15},
            {'threshold': 0.10, 'is_significant': False, 'p_value': 0.15}
        ]

        robustness_results = {
            'with_mmse_filter': {'p_value': 0.14, 'is_significant': False},
            'without_mmse_filter': {'p_value': 0.15, 'is_significant': False}
        }

        report = generate_sensitivity_report(sensitivity_results, robustness_results)

        assert 'sensitivity_analysis' in report
        assert 'robustness_check' in report
        assert 'thresholds_tested' in report['sensitivity_analysis']
        assert 'mmse_filter_comparison' in report['robustness_check']

    def test_generate_sensitivity_report_borderline(self):
        """Test sensitivity report with borderline results."""
        sensitivity_results = [
            {'threshold': 0.04, 'is_significant': False, 'p_value': 0.049},
            {'threshold': 0.05, 'is_significant': True, 'p_value': 0.049},
            {'threshold': 0.06, 'is_significant': True, 'p_value': 0.049}
        ]

        robustness_results = {
            'with_mmse_filter': {'p_value': 0.05, 'is_significant': True},
            'without_mmse_filter': {'p_value': 0.049, 'is_significant': True}
        }

        report = generate_sensitivity_report(sensitivity_results, robustness_results)

        assert report['sensitivity_analysis']['is_stable'] is False
        assert 'borderline' in report['sensitivity_analysis']['assessment'].lower()

    def test_generate_sensitivity_report_stable(self):
        """Test sensitivity report with stable results."""
        sensitivity_results = [
            {'threshold': 0.01, 'is_significant': True, 'p_value': 0.01},
            {'threshold': 0.05, 'is_significant': True, 'p_value': 0.01},
            {'threshold': 0.10, 'is_significant': True, 'p_value': 0.01}
        ]

        robustness_results = {
            'with_mmse_filter': {'p_value': 0.01, 'is_significant': True},
            'without_mmse_filter': {'p_value': 0.01, 'is_significant': True}
        }

        report = generate_sensitivity_report(sensitivity_results, robustness_results)

        assert report['sensitivity_analysis']['is_stable'] is True
        assert report['robustness_check']['is_robust'] is True
