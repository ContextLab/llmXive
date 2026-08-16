import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import json

from code.entanglement_scores import compute_per_sample_stats, calculate_entropy

class TestCalculateEntropy:
    def test_uniform_distribution(self):
        # Uniform distribution over 4 items: prob = 0.25 each
        # Entropy = -4 * (0.25 * log(0.25)) = log(4) ≈ 1.386
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_entropy(probs)
        expected = -4 * (0.25 * np.log(0.25))
        assert np.isclose(entropy, expected)

    def test_deterministic_distribution(self):
        # One item has prob 1, others 0 -> Entropy = 0
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy == 0.0

    def test_all_zeros(self):
        # Edge case: all zeros -> should return 0
        probs = np.array([0.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert entropy == 0.0

class TestComputePerSampleStats:
    @pytest.fixture
    def valid_df(self):
        # Create a valid DataFrame with teacher scores
        data = {
            'Alignment': [5.0, 4.0, 3.0, 5.0],
            'Realism': [4.0, 4.0, 4.0, 5.0],
            'Aesthetics': [4.0, 5.0, 3.0, 5.0],
            'Plausibility': [4.0, 4.0, 4.0, 5.0],
            'other_col': ['a', 'b', 'c', 'd']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def df_with_nan(self):
        data = {
            'Alignment': [5.0, np.nan, 3.0, 5.0],
            'Realism': [4.0, 4.0, np.nan, 5.0],
            'Aesthetics': [4.0, 4.0, 3.0, 5.0],
            'Plausibility': [4.0, 4.0, 4.0, 5.0],
            'other_col': ['a', 'b', 'c', 'd']
        }
        return pd.DataFrame(data)

    def test_basic_computation(self, valid_df):
        result = compute_per_sample_stats(valid_df)
        
        # Check new columns exist
        assert 'variance' in result.columns
        assert 'entropy' in result.columns
        assert 'skewness' in result.columns
        assert 'kurtosis' in result.columns
        
        # Check row count preserved
        assert len(result) == len(valid_df)
        
        # Check variance for first row: [5,4,4,4] -> mean=4.25, var=0.25
        expected_var_0 = np.var([5.0, 4.0, 4.0, 4.0], ddof=0)
        assert np.isclose(result.loc[0, 'variance'], expected_var_0)

    def test_zero_variance_case(self):
        # All scores identical -> variance=0, entropy should be 0 (if normalized)
        data = {
            'Alignment': [5.0, 5.0, 5.0, 5.0],
            'Realism': [5.0, 5.0, 5.0, 5.0],
            'Aesthetics': [5.0, 5.0, 5.0, 5.0],
            'Plausibility': [5.0, 5.0, 5.0, 5.0],
            'other_col': ['a', 'b', 'c', 'd']
        }
        df = pd.DataFrame(data)
        result = compute_per_sample_stats(df)
        
        # Variance should be 0
        assert np.all(result['variance'] == 0.0)
        
        # Entropy for deterministic distribution (after normalization) should be 0
        assert np.all(result['entropy'] == 0.0)

    def test_nan_handling(self, df_with_nan):
        result = compute_per_sample_stats(df_with_nan)
        
        # Row 1 (index 1) has NaN in Alignment -> variance=0, entropy=0, skew/kurt=NaN
        assert result.loc[1, 'variance'] == 0.0
        assert result.loc[1, 'entropy'] == 0.0
        assert np.isnan(result.loc[1, 'skewness'])
        assert np.isnan(result.loc[1, 'kurtosis'])
        
        # Row 2 (index 2) has NaN in Realism -> variance=0, entropy=0, skew/kurt=NaN
        assert result.loc[2, 'variance'] == 0.0
        assert result.loc[2, 'entropy'] == 0.0
        assert np.isnan(result.loc[2, 'skewness'])
        assert np.isnan(result.loc[2, 'kurtosis'])

    def test_missing_columns(self):
        df = pd.DataFrame({'other_col': ['a', 'b']})
        with pytest.raises(RuntimeError, match="Missing required teacher score columns"):
            compute_per_sample_stats(df)

    def test_output_to_csv(self, valid_df, tmp_path):
        input_path = tmp_path / "input.parquet"
        output_path = tmp_path / "output.csv"
        
        valid_df.to_parquet(input_path)
        
        # Run the main logic manually
        result = compute_per_sample_stats(valid_df)
        result.to_csv(output_path, index=False)
        
        assert output_path.exists()
        loaded = pd.read_csv(output_path)
        assert 'variance' in loaded.columns
        assert 'entropy' in loaded.columns
        assert len(loaded) == len(valid_df)