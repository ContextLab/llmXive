import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from imbalance import (
    load_data,
    identify_target_columns,
    calculate_gini,
    calculate_target_imbalance_score,
    calculate_compositional_imbalance_score,
    analyze_all_properties,
    save_results
)

class TestGiniCalculation:
    def test_gini_uniform_distribution(self):
        """Uniform distribution should have Gini near 0."""
        values = np.array([10, 10, 10, 10, 10])
        gini = calculate_gini(values)
        assert abs(gini - 0.0) < 0.01

    def test_gini_uneven_distribution(self):
        """Uneven distribution should have higher Gini."""
        values = np.array([1, 1, 1, 1, 100])
        gini = calculate_gini(values)
        assert gini > 0.5

    def test_gini_negative_values(self):
        """Gini should handle negative values by shifting."""
        values = np.array([-10, -5, 0, 5, 10])
        gini = calculate_gini(values)
        assert 0.0 <= gini <= 1.0

    def test_gini_empty_array(self):
        """Empty array should return 0."""
        values = np.array([])
        gini = calculate_gini(values)
        assert gini == 0.0

class TestCompositionalImbalance:
    def test_cluster_count_gini(self):
        """Test Gini calculation on cluster counts."""
        # Simulate 50 clusters, some empty, some full
        counts = np.array([100, 0, 0, ..., 0]) # Conceptually: 1 cluster with 100, 49 empty
        # Actually create array
        counts = np.zeros(50, dtype=int)
        counts[0] = 100
        gini = calculate_gini(counts)
        # Max Gini for discrete distribution is (N-1)/N
        assert abs(gini - (49/50)) < 0.01

    def test_compositional_score_calculation(self):
        """Test full compositional imbalance calculation with dummy data."""
        # Create dummy descriptor data
        n_samples = 1000
        n_features = 10
        np.random.seed(42)
        
        df = pd.DataFrame({
            'feature_' + str(i): np.random.randn(n_samples) for i in range(n_features)
        })
        df['composition'] = ['A' * i for i in range(n_samples)] # Dummy composition
        
        result = calculate_compositional_imbalance_score(df, n_clusters=5)
        
        assert 'compositional_imbalance_score' in result
        assert 0.0 <= result['compositional_imbalance_score'] <= 1.0

class TestTargetImbalance:
    def test_target_score_calculation(self):
        """Test target imbalance score with dummy data."""
        n_samples = 200
        df = pd.DataFrame({
            'property_a': np.random.randn(n_samples),
            'property_b': np.random.randn(n_samples),
            'composition': ['A' * i for i in range(n_samples)]
        })
        
        target_cols = identify_target_columns(df)
        assert 'property_a' in target_cols
        assert 'property_b' in target_cols
        
        scores = calculate_target_imbalance_score(df, target_cols, min_samples=50)
        assert 'property_a' in scores
        assert 'property_b' in scores

class TestSaveResults:
    def test_save_to_csv(self):
        """Test saving results to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.csv")
            target_scores = {"prop1": 0.5, "prop2": 0.6}
            compositional_scores = {"compositional": 0.3}
            
            save_results(target_scores, compositional_scores, output_path)
            
            assert os.path.exists(output_path)
            df = pd.read_csv(output_path)
            assert len(df) == 3 # 2 target + 1 compositional
            assert "property" in df.columns
            assert "score_type" in df.columns
            assert "score_value" in df.columns