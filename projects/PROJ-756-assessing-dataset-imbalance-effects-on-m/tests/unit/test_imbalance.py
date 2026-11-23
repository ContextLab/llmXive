import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from imbalance import (
    load_data,
    calculate_gini,
    calculate_compositional_imbalance_score,
    calculate_target_imbalance_score,
    identify_target_columns,
    save_results
)

class TestGini:
    def test_gini_equal_distribution(self):
        # Perfect equality -> Gini = 0
        values = np.array([10, 10, 10, 10])
        assert calculate_gini(values) == pytest.approx(0.0, abs=1e-9)

    def test_gini_unequal_distribution(self):
        # High inequality -> Gini > 0
        values = np.array([1, 1, 1, 97])
        gini_val = calculate_gini(values)
        assert 0 < gini_val <= 1.0

    def test_gini_empty_array(self):
        assert calculate_gini(np.array([])) == 0.0

    def test_gini_negative_values(self):
        # Should handle negative values by taking absolute
        values = np.array([-10, -10, -10])
        assert calculate_gini(values) == pytest.approx(0.0, abs=1e-9)

class TestCompositionalImbalance:
    def test_compositional_imbalance_single_cluster(self):
        # If all points fall into one cluster, Gini should be 0 (perfect equality in counts? No, all in one -> counts=[N, 0, 0...] -> Gini=1)
        # Actually, if all in one cluster, counts = [N, 0, 0, ...] -> Gini = 1 (max inequality)
        # Let's test a balanced scenario: equal counts
        n_samples = 100
        n_clusters = 5
        # Create data that will cluster evenly (e.g., 5 distinct groups)
        X = np.vstack([
            np.random.randn(20, 2) + np.array([i*5, i*5]) for i in range(n_clusters)
        ])
        df = pd.DataFrame(X, columns=['feat1', 'feat2'])
        
        # We can't guarantee exact clustering, but we can check the function runs
        score = calculate_compositional_imbalance_score(df, k_clusters=n_clusters)
        assert 0.0 <= score <= 1.0

    def test_compositional_imbalance_empty_df(self):
        df = pd.DataFrame(columns=['feat1', 'feat2'])
        # Should handle empty or raise? Let's assume it raises or returns 0.
        # Based on implementation, if len(feature_cols) == 0 it raises.
        with pytest.raises(ValueError):
            calculate_compositional_imbalance_score(df, k_clusters=5)

    def test_compositional_imbalance_with_nan(self):
        X = np.random.randn(100, 2)
        X[0, 0] = np.nan
        df = pd.DataFrame(X, columns=['feat1', 'feat2'])
        # Should handle NaN by replacing with mean
        score = calculate_compositional_imbalance_score(df, k_clusters=5)
        assert 0.0 <= score <= 1.0

class TestTargetImbalance:
    def test_target_imbalance_skip_small_sample(self):
        df = pd.DataFrame({'target_prop': np.random.randn(50)})
        score = calculate_target_imbalance_score(df, 'target_prop')
        assert score == 0.0

    def test_target_imbalance_valid_sample(self):
        # Create a skewed distribution
        values = np.concatenate([np.ones(900), np.ones(100) * 100]) # 90% low, 10% high
        df = pd.DataFrame({'target_prop': values})
        score = calculate_target_imbalance_score(df, 'target_prop')
        assert 0.0 < score <= 1.0

class TestIdentifyTargets:
    def test_identify_targets(self):
        df = pd.DataFrame({
            'composition': ['A', 'B'],
            'feat1': [1.0, 2.0],
            'target_energy': [10.0, 20.0],
            'target_gap': [1.0, 2.0]
        })
        targets = identify_target_columns(df)
        # Should include feat1, target_energy, target_gap (all numeric except composition)
        assert 'composition' not in targets
        assert len(targets) == 3

class TestSaveResults:
    def test_save_compositional_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            results = {'compositional': 0.5}
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df['score_type'].iloc[0] == 'compositional'
            assert df['score'].iloc[0] == 0.5

    def test_save_target_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.csv")
            results = {'energy': 0.4, 'gap': 0.6}
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert all(df['score_type'] == 'target')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])