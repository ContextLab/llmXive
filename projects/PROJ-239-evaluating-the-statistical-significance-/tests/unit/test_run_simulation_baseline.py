"""
Unit tests for run_simulation_baseline.py
"""

import argparse
import sys
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'code'))

from run_simulation_baseline import parse_args, main
from config import DEFAULT_SEED, ICC_STEP

def test_parse_args_defaults():
    """Test that parse_args returns correct defaults."""
    with patch('sys.argv', ['run_simulation_baseline.py']):
        args = parse_args()
        assert args.iterations == 1000
        assert args.seed == DEFAULT_SEED
        assert args.icc_step == ICC_STEP
        assert args.icc_range_start == 0.0
        assert args.icc_range_end == 0.5
        assert args.output == "data/derived/baseline_results.csv"
        assert args.icc is None

def test_parse_args_custom_values():
    """Test that parse_args correctly overrides defaults."""
    test_args = [
        'run_simulation_baseline.py',
        '--icc', '0.3',
        '--iterations', '500',
        '--seed', '123',
        '--icc-step', '0.05',
        '--icc-range-start', '0.1',
        '--icc-range-end', '0.4',
        '--output', 'custom_output.csv'
    ]
    with patch('sys.argv', test_args):
        args = parse_args()
        assert args.icc == 0.3
        assert args.iterations == 500
        assert args.seed == 123
        assert args.icc_step == 0.05
        assert args.icc_range_start == 0.1
        assert args.icc_range_end == 0.4
        assert args.output == 'custom_output.csv'

def test_main_creates_output_file():
    """Test that main creates the output CSV file with correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_results.csv')
        
        # Mock the simulation functions to return predictable data
        mock_results = [
            {'icc': 0.0, 'p_value': 0.04, 'iteration': 1},
            {'icc': 0.0, 'p_value': 0.06, 'iteration': 2},
            {'icc': 0.1, 'p_value': 0.03, 'iteration': 1},
            {'icc': 0.1, 'p_value': 0.07, 'iteration': 2}
        ]
        
        with patch('run_simulation_baseline.run_baseline_simulation', return_value=mock_results):
            with patch('run_simulation_baseline.aggregate_errors') as mock_agg:
                mock_df = pd.DataFrame({
                    'icc': [0.0, 0.1],
                    'alpha': [0.05, 0.05],
                    'error_rate': [0.5, 0.5],
                    'ci_lower': [0.1, 0.1],
                    'ci_upper': [0.9, 0.9]
                })
                mock_agg.return_value = mock_df
                
                with patch('sys.argv', ['run_simulation_baseline.py', '--output', output_path, '--icc', '0.0', '--iterations', '2']):
                    result = main()
                    
                    assert result == 0
                    assert os.path.exists(output_path)
                    
                    # Read and verify the output file
                    df_output = pd.read_csv(output_path)
                    assert 'icc' in df_output.columns
                    assert 'alpha' in df_output.columns
                    assert 'error_rate' in df_output.columns
                    assert len(df_output) > 0
