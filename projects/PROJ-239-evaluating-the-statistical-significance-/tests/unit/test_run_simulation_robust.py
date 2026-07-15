"""
Unit tests for run_simulation_robust.py script.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.run_simulation_robust import parse_args, main
from code.config import load_config

def test_parse_args_defaults():
    """Test that parse_args returns default values when no args provided."""
    # Mock sys.argv to avoid actual CLI parsing
    import sys
    original_argv = sys.argv
    sys.argv = ['run_simulation_robust.py']
    
    try:
        args = parse_args()
        assert args.iterations == 1000
        assert args.seed == 42
        assert args.output == "data/derived/robustResults.csv"
        assert args.icc is None
        assert args.icc_range is None
        assert args.icc_step is None
        assert args.alpha_list is None
    finally:
        sys.argv = original_argv

def test_parse_args_custom_values():
    """Test that parse_args correctly parses custom CLI arguments."""
    import sys
    original_argv = sys.argv
    sys.argv = [
        'run_simulation_robust.py',
        '--icc', '0.2',
        '--iterations', '500',
        '--seed', '123',
        '--output', 'custom_output.csv',
        '--alpha-list', '0.01', '0.05'
    ]
    
    try:
        args = parse_args()
        assert args.icc == 0.2
        assert args.iterations == 500
        assert args.seed == 123
        assert args.output == 'custom_output.csv'
        assert args.alpha_list == [0.01, 0.05]
    finally:
        sys.argv = original_argv

def test_main_creates_output_file():
    """Test that main() creates the output CSV file with expected structure."""
    import sys
    original_argv = sys.argv
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_robust_results.csv')
        sys.argv = [
            'run_simulation_robust.py',
            '--icc', '0.0',
            '--iterations', '10',
            '--seed', '42',
            '--output', output_path
        ]
        
        try:
            # Run the main function
            result = main()
            
            # Check return code
            assert result == 0
            
            # Check file exists
            assert os.path.exists(output_path)
            
            # Check file contents
            df = pd.read_csv(output_path)
            
            # Verify expected columns
            expected_columns = ['method', 'icc', 'alpha', 'error_rate', 'ci_lower', 'ci_upper']
            for col in expected_columns:
                assert col in df.columns, f"Missing column: {col}"
            
            # Verify data types
            assert df['icc'].dtype in ['float64', 'int64']
            assert df['error_rate'].dtype == 'float64'
            assert df['ci_lower'].dtype == 'float64'
            assert df['ci_upper'].dtype == 'float64'
            
            # Verify we have results for the tested ICC
            assert len(df[df['icc'] == 0.0]) > 0
            
            # Verify we have results for all alpha levels
            for alpha in [0.01, 0.05, 0.10]:
                assert len(df[df['alpha'] == alpha]) > 0
                
        finally:
            sys.argv = original_argv

def test_main_with_multiple_icc_levels():
    """Test main() with multiple ICC levels."""
    import sys
    original_argv = sys.argv
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'multi_icc_results.csv')
        sys.argv = [
            'run_simulation_robust.py',
            '--icc-range', '0.0', '0.2', '0.4',
            '--icc-step', '0.2',
            '--iterations', '5',
            '--seed', '99',
            '--output', output_path
        ]
        
        try:
            result = main()
            assert result == 0
            
            df = pd.read_csv(output_path)
            
            # Should have results for each ICC level
            unique_iccs = df['icc'].unique()
            assert 0.0 in unique_iccs
            assert 0.2 in unique_iccs
            assert 0.4 in unique_iccs
            
            # Should have results for each method (naive, cluster_robust, block_permutation)
            methods = df['method'].unique()
            assert len(methods) >= 3
            
        finally:
            sys.argv = original_argv