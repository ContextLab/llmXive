"""
Contract tests for sensitivity analysis output schema.

Verifies that sensitivity analysis results conform to expected schema.
"""

import pytest
from typing import Dict, Any, Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np

from analysis.sensitivity import run_sensitivity_analysis

class TestSensitivityAnalysisOutput:
    """Test sensitivity analysis output schema compliance."""
    
    def test_output_schema(self, tmp_path):
        """Test that output CSV has required columns."""
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        # Required columns
        required_columns = [
            'token_limit',
            'avg_specialization_index',
            'std_specialization_index',
            'avg_retrieval_efficiency',
            'std_retrieval_efficiency',
            'num_games',
            'valid_games',
            'validation_rate',
            'num_agents'
        ]
        
        for col in required_columns:
            assert col in results_df.columns, f"Missing column: {col}"
    
    def test_token_limits_swept(self, tmp_path):
        """Test that all requested token limits are in output."""
        output_path = tmp_path / 'sensitivity_results.csv'
        token_limits = [128, 256, 512]
        
        results_df = run_sensitivity_analysis(
            token_limits=token_limits,
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        assert len(results_df) == len(token_limits), \
            f"Expected {len(token_limits)} rows, got {len(results_df)}"
        
        assert set(results_df['token_limit'].tolist()) == set(token_limits), \
            "Token limits in output don't match input"
    
    def test_specialization_range(self, tmp_path):
        """Test that specialization indices are in valid range."""
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            num_agents=3,
            output_path=output_path,
            seed=42
        )
        
        max_spec = np.log2(3)  # ~1.585
        
        for spec in results_df['avg_specialization_index']:
            assert 0 <= spec <= max_spec, \
                f"Specialization {spec} out of range [0, {max_spec}]"
    
    def test_retrieval_range(self, tmp_path):
        """Test that retrieval efficiencies are in valid range [0, 1]."""
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        for ret in results_df['avg_retrieval_efficiency']:
            assert 0 <= ret <= 1, f"Retrieval {ret} out of range [0, 1]"
    
    def test_validation_rate(self, tmp_path):
        """Test that validation rates are in valid range [0, 1]."""
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        for rate in results_df['validation_rate']:
            assert 0 <= rate <= 1, f"Validation rate {rate} out of range [0, 1]"
    
    def test_reproducibility(self, tmp_path):
        """Test that results are reproducible with same seed."""
        output_path1 = tmp_path / 'sensitivity_results_1.csv'
        output_path2 = tmp_path / 'sensitivity_results_2.csv'
        
        results_df1 = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path1,
            seed=42
        )
        
        results_df2 = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path2,
            seed=42
        )
        
        assert results_df1['avg_specialization_index'].tolist() == \
               results_df2['avg_specialization_index'].tolist(), \
               "Results not reproducible with same seed"
        
        assert results_df1['avg_retrieval_efficiency'].tolist() == \
               results_df2['avg_retrieval_efficiency'].tolist(), \
               "Results not reproducible with same seed"
    
    def test_std_deviations_non_negative(self, tmp_path):
        """Test that standard deviations are non-negative."""
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        for std in results_df['std_specialization_index']:
            assert std >= 0, f"Standard deviation {std} is negative"
        
        for std in results_df['std_retrieval_efficiency']:
            assert std >= 0, f"Standard deviation {std} is negative"

class TestSensitivityAnalysisPerformance:
    """Test that sensitivity analysis shows expected trends."""
    
    def test_specialization_trend(self, tmp_path):
        """
        Test that specialization index increases with token limit.
        
        With more context, agents can better specialize their roles.
        """
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        # Sort by token limit
        results_df = results_df.sort_values('token_limit')
        
        # Check that specialization generally increases
        specs = results_df['avg_specialization_index'].values
        for i in range(len(specs) - 1):
            assert specs[i+1] >= specs[i] - 0.1, \
                f"Specialization should increase with token limit: {specs[i]} -> {specs[i+1]}"
    
    def test_retrieval_trend(self, tmp_path):
        """
        Test that retrieval efficiency increases with token limit.
        
        With more context, agents have better access to shared memory.
        """
        output_path = tmp_path / 'sensitivity_results.csv'
        
        results_df = run_sensitivity_analysis(
            token_limits=[128, 256, 512],
            num_games=100,
            output_path=output_path,
            seed=42
        )
        
        # Sort by token limit
        results_df = results_df.sort_values('token_limit')
        
        # Check that retrieval generally increases
        rets = results_df['avg_retrieval_efficiency'].values
        for i in range(len(rets) - 1):
            assert rets[i+1] >= rets[i] - 0.1, \
                f"Retrieval should increase with token limit: {rets[i]} -> {rets[i+1]}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])