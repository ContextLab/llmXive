"""
Unit tests for T032: Permutation Null FPR Estimation.

Tests the null dataset generation and FPR estimation logic.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from t032_permutation_null_fpr import (
    generate_null_dataset,
    estimate_fpr_for_dataset,
    load_baseline_metrics,
    write_output
)

class TestGenerateNullDataset:
    """Tests for generate_null_dataset function."""
    
    def test_shuffles_outcome_only(self):
        """Verify that only the outcome column is shuffled."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],
            'y': [10, 20, 30, 40, 50]
        })
        
        result = generate_null_dataset(df, 'y', random_seed=42)
        
        # Predictors should remain unchanged
        assert result['x1'].tolist() == df['x1'].tolist()
        assert result['x2'].tolist() == df['x2'].tolist()
        
        # Outcome should be shuffled (different order)
        assert set(result['y']) == set(df['y'])
        # With high probability, the order will be different
        assert result['y'].tolist() != df['y'].tolist() or len(df) == 1
    
    def test_preserves_row_count(self):
        """Verify that row count is preserved."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 30, 40, 50]
        })
        
        result = generate_null_dataset(df, 'y', random_seed=42)
        assert len(result) == len(df)
    
    def test_reproducibility(self):
        """Verify that same seed produces same result."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [10, 20, 30, 40, 50]
        })
        
        result1 = generate_null_dataset(df, 'y', random_seed=123)
        result2 = generate_null_dataset(df, 'y', random_seed=123)
        
        assert result1['y'].tolist() == result2['y'].tolist()

class TestEstimateFPR:
    """Tests for estimate_fpr_for_dataset function."""
    
    @patch('t032_permutation_null_fpr.run_baseline_analysis')
    def test_fpr_calculation(self, mock_run_baseline):
        """Test FPR calculation with mocked baseline analysis."""
        # Mock baseline analysis to return deterministic results
        mock_run_baseline.return_value = {
            'success': True,
            't_tests': {
                'test1': {'p_value': 0.03},  # Significant
                'test2': {'p_value': 0.15}   # Not significant
            },
            'regressions': {
                'reg1': {'p_values': [0.02, 0.20]}  # One significant
            }
        }
        
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'y': np.random.randn(100)
        })
        
        result = estimate_fpr_for_dataset(
            df_null=df,
            dataset_name='test_dataset',
            outcome_col='y',
            config={'RANDOM_SEED': 42},
            n_permutations=3
        )
        
        assert result['dataset_name'] == 'test_dataset'
        assert result['n_permutations'] == 3
        assert result['t_test_fpr_rate'] >= 0
        assert result['t_test_fpr_rate'] <= 1
        assert result['regression_fpr_rate'] >= 0
        assert result['regression_fpr_rate'] <= 1
    
    @patch('t032_permutation_null_fpr.run_baseline_analysis')
    def test_handles_empty_results(self, mock_run_baseline):
        """Test handling of empty or failed results."""
        mock_run_baseline.return_value = {
            'success': False,
            'error': 'Test error'
        }
        
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'y': np.random.randn(100)
        })
        
        result = estimate_fpr_for_dataset(
            df_null=df,
            dataset_name='test_dataset',
            outcome_col='y',
            config={'RANDOM_SEED': 42},
            n_permutations=2
        )
        
        # Should still return a result with zero FPR
        assert result['t_test_fpr_rate'] == 0.0
        assert result['regression_fpr_rate'] == 0.0

class TestWriteOutput:
    """Tests for write_output function."""
    
    def test_writes_valid_json(self, tmp_path):
        """Test that output is written as valid JSON."""
        output_file = tmp_path / "null_fpr_metrics.json"
        
        results = [
            {
                'dataset_name': 'test1',
                't_test_fpr_rate': 0.05,
                'regression_fpr_rate': 0.03
            }
        ]
        
        write_output(results, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'generated_at' in data
        assert 'datasets' in data
        assert len(data['datasets']) == 1
        assert data['datasets'][0]['dataset_name'] == 'test1'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])