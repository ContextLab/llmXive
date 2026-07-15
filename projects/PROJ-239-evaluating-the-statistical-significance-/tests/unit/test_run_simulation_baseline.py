"""
Unit tests for run_simulation_baseline.py script logic.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.run_simulation_baseline import main
from code.config import load_config
from code.analysis import aggregate_errors
from code.simulation_runner import run_baseline_simulation

def test_main_creates_output_files():
    """
    Test that main() creates the expected output CSV files.
    """
    # Mock the simulation to return known data quickly
    mock_results = [
        {'iteration': 1, 'p_value': 0.03, 'rejected': True},
        {'iteration': 2, 'p_value': 0.15, 'rejected': False},
        {'iteration': 3, 'p_value': 0.01, 'rejected': True},
    ]

    with patch('code.run_simulation_baseline.run_baseline_simulation', return_value=mock_results):
        with patch('code.run_simulation_baseline.aggregate_errors') as mock_agg:
            mock_agg.return_value = pd.DataFrame({
                'alpha': [0.05],
                'method': ['naive'],
                'error_rate': [0.66],
                'ci_lower': [0.30],
                'ci_upper': [0.90]
            })

            # Run main with specific args
            with patch('sys.argv', ['run_simulation_baseline.py', '--icc', '0.1', '--iterations', '3', '--seed', '42']):
                exit_code = main()

            assert exit_code == 0
            assert os.path.exists('data/derived/baseline_results.csv')
            assert os.path.exists('data/derived/baseline_summary.csv')

            # Verify content
            df = pd.read_csv('data/derived/baseline_results.csv')
            assert len(df) == 3
            assert list(df.columns) == ['iteration', 'icc', 'p_value', 'rejected']
            assert df['icc'].iloc[0] == 0.1

            # Cleanup
            os.remove('data/derived/baseline_results.csv')
            os.remove('data/derived/baseline_summary.csv')

def test_main_handles_empty_results():
    """
    Test that main() handles cases where simulation returns no results gracefully.
    """
    with patch('code.run_simulation_baseline.run_baseline_simulation', return_value=[]):
        with patch('sys.argv', ['run_simulation_baseline.py', '--icc', '0.1', '--iterations', '10', '--seed', '42']):
            exit_code = main()

        assert exit_code == 0
        assert os.path.exists('data/derived/baseline_results.csv')
        
        df = pd.read_csv('data/derived/baseline_results.csv')
        assert len(df) == 0

        # Cleanup
        os.remove('data/derived/baseline_results.csv')
        if os.path.exists('data/derived/baseline_summary.csv'):
            os.remove('data/derived/baseline_summary.csv')