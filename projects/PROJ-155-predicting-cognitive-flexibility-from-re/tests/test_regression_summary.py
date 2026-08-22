"""
Tests for T034: Regression Summary Generation.
"""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest

from code.analysis.regression_summary_generator import (
    generate_regression_summary,
    save_regression_summary,
    run_regression_summary_pipeline
)
from code.data.paths import get_results_path


@pytest.fixture
def mock_regression_data():
    """Create a mock dataframe for regression testing."""
    np.random.seed(42)
    n = 100
    data = {
        'Subject_ID': [f'SUBJ_{i:03d}' for i in range(n)],
        'Variability_Metric': np.random.randn(n) * 0.5,
        'Flexibility_Score': np.random.randn(n) * 10 + 50,
        'Age': np.random.randint(18, 65, n),
        'Sex': np.random.choice(['M', 'F'], n),
        'Mean_FD': np.random.rand(n) * 0.2,
        'Total_Scan_Time': np.random.randint(600, 900, n)
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_regression_results():
    """Mock the regression stats dictionary."""
    return {
        'beta': 0.45,
        'se': 0.12,
        'r': 0.6,
        'p_value': 0.003
    }


@pytest.fixture
def mock_permutation_results():
    """Mock permutation test results."""
    return {
        'p_value': 0.004,
        'n_permutations': 10000
    }


def test_generate_regression_summary_structure(
    mock_regression_data,
    mock_regression_results,
    mock_permutation_results
):
    """Test that the generated summary has the correct structure and keys."""
    with patch('code.analysis.regression_summary_generator.load_regression_dataset', return_value=mock_regression_data), \
         patch('code.analysis.regression_summary_generator.run_linear_regression', return_value=mock_regression_results), \
         patch('code.analysis.regression_summary_generator.run_permutation_test', return_value=mock_permutation_results), \
         patch('code.analysis.regression_summary_generator.calculate_success_rate', return_value=0.85):
        
        summary = generate_regression_summary()
        
        # Check top-level keys
        assert 'model_type' in summary
        assert 'coefficients' in summary
        assert 'significance' in summary
        assert 'validation' in summary
        assert 'pipeline_metrics' in summary
        
        # Check coefficients
        assert 'variability_beta' in summary['coefficients']
        assert 'variability_se' in summary['coefficients']
        assert 'r_squared' in summary['coefficients']
        assert 'r' in summary['coefficients']
        
        # Check significance
        assert 'p_value_raw' in summary['significance']
        assert 'is_significant' in summary['significance']
        assert summary['significance']['is_significant'] is True
        
        # Check validation
        assert 'permutation_test' in summary['validation']
        assert summary['validation']['permutation_test']['n_permutations'] == 10000
        
        # Check pipeline metrics
        assert 'pro_processed' in summary['pipeline_metrics']
        assert summary['pipeline_metrics']['pro_processed'] == 0.85


def test_save_regression_summary_creates_file(
    mock_regression_data,
    mock_regression_results,
    mock_permutation_results
):
    """Test that the summary is saved to a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_summary.json")
        
        with patch('code.analysis.regression_summary_generator.load_regression_dataset', return_value=mock_regression_data), \
             patch('code.analysis.regression_summary_generator.run_linear_regression', return_value=mock_regression_results), \
             patch('code.analysis.regression_summary_generator.run_permutation_test', return_value=mock_permutation_results), \
             patch('code.analysis.regression_summary_generator.calculate_success_rate', return_value=0.90), \
             patch('code.analysis.regression_summary_generator.get_results_path', return_value=output_path), \
             patch('code.analysis.regression_summary_generator.ensure_dir'):
            
            summary = generate_regression_summary()
            save_path = save_regression_summary(summary, output_path)
            
            assert os.path.exists(save_path)
            
            with open(save_path, 'r') as f:
                loaded = json.load(f)
                
            assert loaded == summary


def test_p_value_formatting():
    """Test that very small p-values are formatted correctly."""
    # This is implicitly tested in generate_regression_summary via format_p_value
    # but we can verify the logic if needed.
    # The format_p_value function is imported from code.analysis.p_value_formatter
    from code.analysis.p_value_formatter import format_p_value
    
    assert format_p_value(0.05) == "0.0500"
    assert format_p_value(0.00001) == "< 0.0001"
    assert format_p_value(1.0) == "1.0000"