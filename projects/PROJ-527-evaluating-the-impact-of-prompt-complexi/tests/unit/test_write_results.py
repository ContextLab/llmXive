"""
Unit tests for T030: Write execution results to CSV
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from execution.write_results import (
    load_execution_results_from_parquet,
    run_execution_and_analysis,
    write_results_to_csv
)


@patch('execution.write_results.load_variants_from_parquet')
def test_load_execution_results_from_parquet(mock_load_variants, tmp_path):
    """Test loading variants from parquet file."""
    # Mock data
    mock_df = pd.DataFrame({
        'problem_id': ['problem_1', 'problem_2'],
        'complexity_label': ['simple', 'complex'],
        'generated_code': ['code1', 'code2']
    })
    mock_load_variants.return_value = mock_df
    
    # Mock path existence
    with patch('execution.write_results.Paths') as mock_paths:
        mock_paths.PROCESSED_DIR = tmp_path
        with patch('pathlib.Path.exists', return_value=True):
            result = load_execution_results_from_parquet()
            
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert list(result.columns) == ['problem_id', 'complexity_label', 'generated_code']


def test_run_execution_and_analysis():
    """Test execution and analysis pipeline."""
    # Mock input data
    df = pd.DataFrame({
        'problem_id': ['prob_1', 'prob_2'],
        'complexity_label': ['simple', 'complex'],
        'generated_code': ['def foo(): pass', 'def bar(): return 42']
    })
    
    with patch('execution.write_results.execute_sample') as mock_exec, \
         patch('execution.write_results.analyze_generated_code') as mock_static:
        
        # Mock execution results
        mock_exec.side_effect = [
            {'pass_count': 1, 'total_tests': 1, 'status': 'passed', 'exception_type': None, 'timeout': False},
            {'pass_count': 0, 'total_tests': 1, 'status': 'failed', 'exception_type': None, 'timeout': False}
        ]
        
        # Mock static analysis results
        mock_static.side_effect = [
            {'cyclomatic_complexity': 1, 'lines_of_code': 1, 'indentation_issues': 0, 'security_issues': 0},
            {'cyclomatic_complexity': 1, 'lines_of_code': 1, 'indentation_issues': 0, 'security_issues': 0}
        ]
        
        result = run_execution_and_analysis(df)
        
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert 'pass_rate' in result.columns
    assert 'cyclomatic_complexity' in result.columns
    assert result.iloc[0]['status'] == 'passed'
    assert result.iloc[1]['status'] == 'failed'


def test_write_results_to_csv(tmp_path):
    """Test writing results to CSV."""
    df = pd.DataFrame({
        'problem_id': ['prob_1'],
        'complexity_label': ['simple'],
        'pass_count': [1],
        'total_tests': [1],
        'pass_rate': [1.0],
        'status': ['passed'],
        'exception_type': [None],
        'timeout': [False],
        'cyclomatic_complexity': [1],
        'lines_of_code': [1],
        'indentation_issues': [0],
        'security_issues': [0],
        'timestamp': ['2024-01-01T00:00:00']
    })
    
    output_path = tmp_path / "test_results.csv"
    
    result_path = write_results_to_csv(df, output_path)
    
    assert result_path.exists()
    assert result_path == output_path
    
    # Verify CSV content
    loaded_df = pd.read_csv(output_path)
    assert len(loaded_df) == 1
    assert loaded_df.iloc[0]['problem_id'] == 'prob_1'
    assert loaded_df.iloc[0]['pass_rate'] == 1.0