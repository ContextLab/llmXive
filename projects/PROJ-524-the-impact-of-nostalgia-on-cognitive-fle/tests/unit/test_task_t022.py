"""
Unit tests for code/task_t022_generate_report.py.
Tests statistical report generation.
"""
import pytest
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t022_generate_report import (
    compile_final_report
)


class TestCompileFinalReport:
    def test_compile_final_report_basic(self):
        """Test basic final report compilation."""
        cleaned_data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
            'perseverative_errors': [10, 15, 12],
            'categories_completed': [5, 4, 6],
            'age': [65, 70, 75]
        })

        statistical_results = {
            'perseverative_errors': {
                'p_value': 0.03,
                'corrected_p_value': 0.06,
                'cohens_d': 0.5,
                'power': 0.85,
                'mdes': 0.3
            }
        }

        power_results = {
            'overall_power': 0.85,
            'mdes': 0.3
        }

        report = compile_final_report(cleaned_data, statistical_results, power_results)

        assert 'summary' in report
        assert 'statistical_findings' in report
        assert 'power_analysis' in report
        assert 'conclusion' in report

    def test_compile_final_report_with_multiple_metrics(self):
        """Test report with multiple cognitive metrics."""
        cleaned_data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control'],
            'perseverative_errors': [10, 15, 12, 18],
            'categories_completed': [5, 4, 6, 3],
            'age': [65, 70, 75, 80]
        })

        statistical_results = {
            'perseverative_errors': {
                'p_value': 0.03,
                'cohens_d': 0.5
            },
            'categories_completed': {
                'p_value': 0.01,
                'cohens_d': 0.8
            }
        }

        power_results = {
            'overall_power': 0.85,
            'mdes': 0.3
        }

        report = compile_final_report(cleaned_data, statistical_results, power_results)

        assert 'perseverative_errors' in report['statistical_findings']
        assert 'categories_completed' in report['statistical_findings']

    def test_compile_final_report_empty_data(self):
        """Test report with empty cleaned data."""
        cleaned_data = pd.DataFrame()
        statistical_results = {}
        power_results = {}

        report = compile_final_report(cleaned_data, statistical_results, power_results)

        assert 'summary' in report
        assert 'conclusion' in report
        assert 'no_data' in report['summary'].lower() or len(report) > 0
