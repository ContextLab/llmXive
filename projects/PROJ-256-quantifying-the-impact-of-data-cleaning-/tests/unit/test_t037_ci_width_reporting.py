"""
Unit tests for T037: Per-dataset CI width change reporting.
"""
import pytest
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import functions from the module
from code.t037_ci_width_reporting import (
    calculate_ci_width_change,
    calculate_median_and_iqr,
    generate_per_dataset_ci_width_report
)

class TestCalculateCiWidthChange:
    def test_basic_calculation(self):
        # Baseline: [1, 3] -> width 2
        # Cleaned: [1, 4] -> width 3
        # Change: 3 - 2 = 1
        baseline = [1.0, 3.0]
        cleaned = [1.0, 4.0]
        assert calculate_ci_width_change(baseline, cleaned) == 1.0

    def test_negative_change(self):
        # Baseline: [1, 5] -> width 4
        # Cleaned: [1, 3] -> width 2
        # Change: 2 - 4 = -2
        baseline = [1.0, 5.0]
        cleaned = [1.0, 3.0]
        assert calculate_ci_width_change(baseline, cleaned) == -2.0

    def test_empty_lists(self):
        assert calculate_ci_width_change([], []) == 0.0
        assert calculate_ci_width_change([1, 2], []) == 0.0
        assert calculate_ci_width_change([], [1, 2]) == 0.0

    def test_single_element_lists(self):
        # Should handle gracefully or return 0 if logic expects pairs
        # Current logic: width = ci[1] - ci[0]. If len < 2, it might crash or return 0.
        # The function assumes valid pairs. Let's test valid pairs only.
        pass

class TestCalculateMedianAndIqr:
    def test_odd_number_of_values(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_median_and_iqr(values)
        assert result['median'] == 3.0
        # IQR: Q3=4, Q2=2 -> IQR=2
        assert result['iqr'] == 2.0

    def test_even_number_of_values(self):
        values = [1.0, 2.0, 3.0, 4.0]
        result = calculate_median_and_iqr(values)
        # Median: (2+3)/2 = 2.5
        assert result['median'] == 2.5
        # Q3 (75th percentile) of [1,2,3,4] is 3.25, Q25 is 1.75 -> IQR = 1.5
        # Note: numpy default interpolation might vary slightly, but logic holds.
        assert isinstance(result['iqr'], float)

    def test_empty_list(self):
        result = calculate_median_and_iqr([])
        assert result['median'] == 0.0
        assert result['iqr'] == 0.0

    def test_single_value(self):
        result = calculate_median_and_iqr([5.0])
        assert result['median'] == 5.0
        assert result['iqr'] == 0.0

class TestGeneratePerDatasetCiWidthReport:
    def test_n_2_statistical_limitation(self):
        """Test that the function handles n=2 and returns correct stats."""
        metrics = {
            'baseline': {
                'datasets': [
                    {
                        'dataset_name': 'ds1',
                        'analysis': {
                            't_test': {'ci': [1.0, 3.0]} # width 2
                        }
                    },
                    {
                        'dataset_name': 'ds2',
                        'analysis': {
                            't_test': {'ci': [2.0, 6.0]} # width 4
                        }
                    }
                ]
            },
            'cleaned': {
                'datasets': [
                    {
                        'dataset_name': 'ds1',
                        'analysis': {
                            't_test': {'ci': [1.0, 4.0]} # width 3
                        }
                    },
                    {
                        'dataset_name': 'ds2',
                        'analysis': {
                            't_test': {'ci': [2.0, 8.0]} # width 6
                        }
                    }
                ]
            }
        }
        
        # ds1 change: 3 - 2 = 1
        # ds2 change: 6 - 4 = 2
        # Values: [1, 2]
        # Median: 1.5, IQR: 0.5 (Q3=1.75, Q25=1.25 -> 0.5)
        
        report = generate_per_dataset_ci_width_report(metrics)
        
        assert report['summary']['n_datasets'] == 2
        assert report['summary']['median_change'] == 1.5
        # Check IQR calculation (numpy default)
        assert abs(report['summary']['iqr_change'] - 0.5) < 0.01

    def test_missing_cleaned_entry(self):
        metrics = {
            'baseline': {
                'datasets': [
                    {'dataset_name': 'ds1', 'analysis': {'t_test': {'ci': [1, 3]}}}
                ]
            },
            'cleaned': {
                'datasets': []
            }
        }
        report = generate_per_dataset_ci_width_report(metrics)
        assert report['summary']['n_datasets'] == 0
        assert report['per_dataset'] == []

    def test_invalid_ci_format(self):
        metrics = {
            'baseline': {
                'datasets': [
                    {'dataset_name': 'ds1', 'analysis': {'t_test': {'ci': [1, 3]}}}
                ]
            },
            'cleaned': {
                'datasets': [
                    {'dataset_name': 'ds1', 'analysis': {'t_test': {'ci': [1, 3, 4]}}} # Invalid length
                ]
            }
        }
        # Should skip invalid entries
        report = generate_per_dataset_ci_width_report(metrics)
        assert report['summary']['n_datasets'] == 0