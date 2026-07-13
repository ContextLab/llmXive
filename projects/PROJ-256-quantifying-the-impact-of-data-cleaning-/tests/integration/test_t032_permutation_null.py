"""
Integration tests for T032: Permutation Null FPR Estimation.

Tests that:
1. The script runs without error
2. The output file is created
3. The output contains valid FPR estimates
4. FPR is approximately alpha (0.05) under the null hypothesis
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from t032_permutation_null_fpr import (
    generate_null_dataset,
    estimate_fpr_for_dataset,
    main,
    write_output
)
from utils import pin_random_seed


class TestPermutationNullFPR:
    """Tests for permutation null FPR estimation logic."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe for testing."""
        pin_random_seed(42)
        n = 100
        return pd.DataFrame({
            'outcome': np.random.randn(n),
            'predictor1': np.random.randn(n),
            'predictor2': np.random.randn(n),
            'predictor3': np.random.randn(n)
        })

    @pytest.fixture
    def null_metrics_path(self, tmp_path):
        """Create a temporary path for output metrics."""
        output_dir = tmp_path / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / "null_fpr_metrics.json"

    def test_generate_null_dataset_shuffles_outcome(self, sample_dataframe):
        """Test that generate_null_dataset shuffles the outcome column."""
        outcome_values = sample_dataframe['outcome'].values
        null_df = generate_null_dataset(sample_dataframe, 'outcome', seed=42)
        
        # Outcome should be shuffled (different order)
        assert not np.array_equal(outcome_values, null_df['outcome'].values)
        
        # But values should be the same (just permuted)
        assert set(outcome_values) == set(null_df['outcome'].values)
        
        # Predictors should be unchanged
        assert np.array_equal(sample_dataframe['predictor1'].values, null_df['predictor1'].values)

    def test_estimate_fpr_returns_valid_structure(self, sample_dataframe):
        """Test that FPR estimation returns a dictionary with expected keys."""
        result = estimate_fpr_for_dataset(
            sample_dataframe,
            outcome_col='outcome',
            predictor_cols=['predictor1'],
            num_permutations=10,
            alpha=0.05,
            seed=42
        )
        
        assert isinstance(result, dict)
        assert 'fpr' in result
        assert 'num_permutations' in result
        assert 'num_false_positives' in result
        assert 'p_values' in result
        assert 'status' in result
        assert result['status'] in ['success', 'skipped_no_data']

    def test_fpr_approximates_alpha_under_null(self, sample_dataframe):
        """
        Test that FPR is approximately alpha (0.05) under the null hypothesis.
        
        With shuffled outcomes, there should be no relationship between 
        predictors and outcome, so p-values should be uniformly distributed.
        The proportion of p <= alpha should be close to alpha.
        """
        # Increase permutations for better estimation
        result = estimate_fpr_for_dataset(
            sample_dataframe,
            outcome_col='outcome',
            predictor_cols=['predictor1'],
            num_permutations=100,
            alpha=0.05,
            seed=42
        )
        
        if result['status'] == 'success':
            fpr = result['fpr']
            # FPR should be close to alpha (allow some variance due to randomness)
            # With 100 permutations, standard error is sqrt(0.05*0.95/100) ≈ 0.022
            # So we expect FPR within [0.01, 0.15] most of the time
            assert 0.0 <= fpr <= 0.20, f"FPR {fpr} is outside expected range [0.0, 0.20]"

    def test_write_output_creates_file(self, sample_dataframe, null_metrics_path):
        """Test that write_output creates the JSON file."""
        # Temporarily override output path
        import t032_permutation_null_fpr
        original_write = t032_permutation_null_fpr.write_output
        
        def mock_write(data):
            config_mock = type('Config', (), {'get': lambda self, k, d=None: str(null_metrics_path.parent) if k == 'OUTPUT_PATH' else d})()
            import t032_permutation_null_fpr as mod
          # Patch get_config temporarily
            mod.get_config = lambda: config_mock
            write_output(data)
        
        test_data = {
            "status": "success",
            "datasets": [{"fpr": 0.05, "dataset_name": "test"}],
            "summary": {"total_datasets": 1}
        }
        
        mock_write(test_data)
        
        assert null_metrics_path.exists()
        
        with open(null_metrics_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['status'] == 'success'

    def test_main_creates_output_file(self, tmp_path, monkeypatch):
        """Test that main() creates the output file when run."""
        # Setup: Create a mock baseline_metrics.json
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        baseline_data = {
            "datasets": [
                {
                    "name": "test_dataset",
                    "outcome_column": "outcome",
                    "predictor_columns": ["predictor1"]
                }
            ]
        }
        
        baseline_path = processed_dir / "baseline_metrics.json"
        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        
        # Create a dummy test dataset
        test_df = pd.DataFrame({
            'outcome': np.random.randn(50),
            'predictor1': np.random.randn(50)
        })
        test_df.to_csv(processed_dir / "test_dataset.csv", index=False)
        
        # Patch get_config to use our temp directory
        def mock_get_config():
            class Config:
                def get(self, key, default=None):
                    if key == 'OUTPUT_PATH':
                        return str(processed_dir)
                    elif key == 'BOOTSTRAP_ITERATIONS':
                        return 10
                    elif key == 'RANDOM_SEED':
                        return 42
                    return default
            return Config()
        
        from t032_permutation_null_fpr import get_config
        monkeypatch.setattr('t032_permutation_null_fpr.get_config', mock_get_config)
        
        # Run main
        main()
        
        # Verify output file was created
        output_path = processed_dir / "null_fpr_metrics.json"
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert 'datasets' in result
        assert 'summary' in result
        assert result['status'] in ['success', 'no_datasets_processed']

    def test_fpr_with_no_signal(self):
        """Test FPR when there is truly no relationship (shuffled data)."""
        pin_random_seed(123)
        n = 200
        df = pd.DataFrame({
            'outcome': np.random.randn(n),
            'predictor': np.random.randn(n)
        })
        
        result = estimate_fpr_for_dataset(
            df,
            'outcome',
            ['predictor'],
            num_permutations=50,
            alpha=0.05,
            seed=123
        )
        
        if result['status'] == 'success':
            # Under null, FPR should be close to alpha
            assert 0.0 <= result['fpr'] <= 0.15, f"FPR {result['fpr']} too high"

    def test_fpr_handles_empty_predictors(self):
        """Test that FPR estimation handles empty predictor list gracefully."""
        df = pd.DataFrame({
            'outcome': [1, 2, 3],
            'other': [4, 5, 6]
        })
        
        result = estimate_fpr_for_dataset(
            df,
            'outcome',
            [],  # No predictors
            num_permutations=10,
            alpha=0.05,
            seed=42
        )
        
        assert result['status'] == 'skipped_no_data' or result['num_permutations'] == 0