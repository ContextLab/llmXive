import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from analysis.metrics import calculate_aggregate_metrics, calculate_confidence_interval, run_full_analysis_pipeline

class TestConfidenceInterval:
    def test_clopper_pearson(self):
        # Test with known values
        # n=100, p=0.05 -> expected CI around [0.01, 0.11]
        low, high = calculate_confidence_interval(0.05, 100)
        assert 0.01 <= low <= 0.02
        assert 0.10 <= high <= 0.12

class TestEmpiricalErrorRate:
    def test_aggregate_metrics(self):
        # Create a dummy dataframe
        data = {
            'p_value': [0.01, 0.06, 0.03, 0.08],
            'reject_null': [True, False, True, False],
            'scaling': ['std', 'std', 'std', 'std'],
            'test_type': ['t_test', 't_test', 't_test', 't_test']
        }
        df = pd.DataFrame(data)
        
        metrics = calculate_aggregate_metrics(df)
        key = "std_t_test"
        assert key in metrics
        assert metrics[key]['total_iterations'] == 4
        assert metrics[key]['rejections'] == 2
        assert metrics[key]['empirical_rate'] == 0.5

class TestFullPipeline:
    def test_run_full_analysis_pipeline(self):
        # Test that run_full_analysis_pipeline accepts results_df
        data = {
            'p_value': [0.01, 0.06],
            'reject_null': [True, False],
            'scaling': ['std', 'std'],
            'test_type': ['t_test', 't_test']
        }
        df = pd.DataFrame(data)
        
        # This should not raise an error
        metrics = run_full_analysis_pipeline(df)
        assert 'std_t_test' in metrics
        assert metrics['std_t_test']['empirical_rate'] == 0.5