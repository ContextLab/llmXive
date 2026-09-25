"""
Unit tests for analyze.py module.

Tests:
- T016: Spearman correlation computation and CI
- T019: Ordinal regression with controls
- T017: Associational framing
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze import (
    load_consistency_scores,
    compute_spearman_correlation,
    compute_ordinal_regression,
    format_associational_framing,
    save_analysis_results
)

class TestLoadConsistencyScores:
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid consistency scores file."""
        # Create test data
        data = {
            'interaction_id': [1, 2, 3],
            'consistency_score': [0.8, 0.6, 0.9],
            'trust_score': [4, 3, 5]
        }
        df = pd.DataFrame(data)
        input_path = tmp_path / "test_scores.csv"
        df.to_csv(input_path, index=False)
        
        # Load and verify
        loaded_df = load_consistency_scores(str(input_path))
        assert len(loaded_df) == 3
        assert 'consistency_score' in loaded_df.columns
        assert 'trust_score' in loaded_df.columns
    
    def test_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_consistency_scores(str(tmp_path / "nonexistent.csv"))
    
    def test_missing_columns(self, tmp_path):
        """Test that missing columns raise ValueError."""
        data = {'interaction_id': [1, 2]}
        df = pd.DataFrame(data)
        input_path = tmp_path / "bad_scores.csv"
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError):
            load_consistency_scores(str(input_path))

class TestComputeSpearmanCorrelation:
    def test_perfect_correlation(self):
        """Test with perfectly correlated data."""
        data = {
            'consistency_score': [1, 2, 3, 4, 5],
            'trust_score': [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        result = compute_spearman_correlation(df)
        
        assert result['coefficient'] == pytest.approx(1.0, abs=0.01)
        assert result['p_value'] < 0.05
        assert result['n_samples'] == 5
    
    def test_no_correlation(self):
        """Test with uncorrelated data."""
        np.random.seed(42)
        data = {
            'consistency_score': np.random.rand(100),
            'trust_score': np.random.rand(100)
        }
        df = pd.DataFrame(data)
        
        result = compute_spearman_correlation(df)
        
        # With random data, rho should be close to 0
        assert abs(result['coefficient']) < 0.2
        assert 'ci_lower' in result
        assert 'ci_upper' in result
    
    def test_insufficient_samples(self):
        """Test with too few samples."""
        data = {
            'consistency_score': [1.0, 2.0],
            'trust_score': [1.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_spearman_correlation(df)
        
        assert np.isnan(result['coefficient'])
        assert result['n_samples'] == 2

class TestComputeOrdinalRegression:
    def test_regression_with_controls(self, tmp_path):
        """Test ordinal regression with control variables."""
        np.random.seed(42)
        n = 100
        data = {
            'trust_score': np.random.randint(1, 6, n),
            'consistency_score': np.random.rand(n),
            'avatar_type': np.random.choice(['human', 'robot'], n),
            'duration': np.random.randint(10, 60, n),
            'difficulty': np.random.randint(1, 5, n)
        }
        df = pd.DataFrame(data)
        
        result = compute_ordinal_regression(
            df,
            control_cols=['avatar_type', 'duration', 'difficulty']
        )
        
        assert 'coefficients' in result
        assert 'p_values' in result
        assert 'pseudo_r2' in result
        assert result['n_samples'] == n
    
    def test_insufficient_samples_regression(self):
        """Test regression with too few samples."""
        data = {
            'trust_score': [1, 2],
            'consistency_score': [0.5, 0.6]
        }
        df = pd.DataFrame(data)
        
        result = compute_ordinal_regression(df)
        
        assert result['n_samples'] == 2
        assert np.isnan(result['pseudo_r2'])

class TestAssociationalFraming:
    def test_correlation_framing(self):
        """Test that correlation results are framed as associational."""
        results = {
            'coefficient': 0.75,
            'p_value': 0.001,
            'ci_lower': 0.65,
            'ci_upper': 0.85,
            'n_samples': 100
        }
        
        framing = format_associational_framing(results, 'correlation')
        
        assert 'ASSOCIATION' in framing
        assert 'NO causal inference' in framing
        assert 'Associational Only' in framing
    
    def test_regression_framing(self):
        """Test that regression results are framed as associational."""
        results = {
            'pseudo_r2': 0.45,
            'n_samples': 200,
            'converged': True
        }
        
        framing = format_associational_framing(results, 'regression')
        
        assert 'ASSOCIATIONS' in framing
        assert 'NO causal inference' in framing
        assert 'Associational Only' in framing

class TestSaveAnalysisResults:
    def test_save_correlation_results(self, tmp_path):
        """Test saving correlation results to CSV and JSON."""
        results = {
            'coefficient': 0.75,
            'p_value': 0.001,
            'ci_lower': 0.65,
            'ci_upper': 0.85,
            'n_samples': 100
        }
        
        output_path = str(tmp_path / "results.csv")
        save_analysis_results(results, output_path, 'correlation')
        
        # Verify CSV exists
        assert os.path.exists(output_path)
        
        # Verify JSON exists
        json_path = output_path.replace('.csv', '.json')
        assert os.path.exists(json_path)
        
        # Verify content
        df = pd.read_csv(output_path)
        assert len(df) == 5
        assert 'metric' in df.columns
        assert 'value' in df.columns
    
    def test_save_regression_results(self, tmp_path):
        """Test saving regression results."""
        results = {
            'coefficients': {'const': 1.0, 'consistency_score': 0.5},
            'p_values': {'const': 0.01, 'consistency_score': 0.03},
            'pseudo_r2': 0.45,
            'n_samples': 100,
            'converged': True
        }
        
        output_path = str(tmp_path / "regression_results.csv")
        save_analysis_results(results, output_path, 'regression')
        
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)
        assert 'variable' in df.columns
        assert 'coefficient' in df.columns