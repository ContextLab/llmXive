"""
Unit tests for the permutation test implementation (T030a).
"""
import pytest
import numpy as np
import pandas as pd
import json
import pickle
import os
import tempfile
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

# Import the functions to test
import sys
sys.path.insert(0, 'code')
from permutation_test import r2_score, calculate_permutation_pvalue, run_permutation_test, parse_args

class TestR2Score:
    def test_perfect_prediction(self):
        y_true = [1, 2, 3, 4, 5]
        y_pred = [1, 2, 3, 4, 5]
        assert r2_score(y_true, y_pred) == 1.0

    def test_mean_prediction(self):
        y_true = [1, 2, 3, 4, 5]
        y_pred = [3, 3, 3, 3, 3] # Mean of y_true
        # R2 should be 0
        assert abs(r2_score(y_true, y_pred)) < 1e-6

    def test_worse_than_mean(self):
        y_true = [1, 2, 3, 4, 5]
        y_pred = [5, 4, 3, 2, 1] # Inverse
        r2 = r2_score(y_true, y_pred)
        assert r2 < 0

class TestPermutationPvalue:
    def setup_method(self):
        """Set up a simple dataset and model for testing."""
        np.random.seed(42)
        self.X = np.random.rand(100, 5)
        # Create a target with some correlation to X
        self.y = 2 * self.X[:, 0] + 0.5 * self.X[:, 1] + np.random.normal(0, 0.1, 100)
        
        self.model = RandomForestRegressor(n_estimators=10, random_state=42)
        self.model.fit(self.X, self.y)

    def test_pvalue_computation(self):
        """Test that the function returns a valid p-value between 0 and 1."""
        p_val = calculate_permutation_pvalue(
            self.X, self.y, self.model, n_permutations=50, random_state=42
        )
        assert 0.0 <= p_val <= 1.0

    def test_deterministic_with_seed(self):
        """Test that the result is deterministic with the same seed."""
        p1 = calculate_permutation_pvalue(
            self.X, self.y, self.model, n_permutations=50, random_state=123
        )
        p2 = calculate_permutation_pvalue(
            self.X, self.y, self.model, n_permutations=50, random_state=123
        )
        assert p1 == p2

    def test_high_pvalue_for_random_model(self):
        """
        If we permute y significantly, or if the model has no predictive power,
        the p-value should be high (close to 1 if the model is random).
        Here we test with a model trained on shuffled y, which should yield high p-value
        when compared to the observed R2 of the original model (which is good).
        Actually, the test is: observed R2 vs permuted R2.
        If the model is good, observed R2 is high. Permuted R2 should be low.
        So p-value (fraction of permuted >= observed) should be low.
        
        Let's test the opposite: Train a model on random noise (no correlation).
        Then observed R2 will be low. Permuted R2 will also be low.
        The p-value should be around 0.5 or higher (random chance).
        """
        X_noise = np.random.rand(50, 5)
        y_noise = np.random.rand(50)
        model_noise = RandomForestRegressor(n_estimators=5, random_state=42)
        model_noise.fit(X_noise, y_noise)
        
        p_val = calculate_permutation_pvalue(
            X_noise, y_noise, model_noise, n_permutations=100, random_state=42
        )
        # With no real signal, p-value should not be extremely small (e.g. < 0.05)
        # It's a random variable, but statistically likely > 0.05
        assert p_val > 0.05

class TestRunPermutationTest:
    def test_end_to_end(self):
        """Test the full pipeline with temporary files."""
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Prepare data
            df = pd.DataFrame({
                'fidelity_loss': np.random.rand(50),
                'feat1': np.random.rand(50),
                'feat2': np.random.rand(50),
                'sample_id': range(50)
            })
            
            # Create split config (indices 0-39 as train)
            split_config = {'train_indices': list(range(40))}
            
            # Train a dummy model
            model = RandomForestRegressor(n_estimators=5, random_state=42)
            model.fit(df.iloc[:40, 1:3].values, df.iloc[:40, 0].values)
            
            # Save files
            features_path = tmpdir / "data.parquet"
            split_path = tmpdir / "split.json"
            model_path = tmpdir / "model.pkl"
            output_path = tmpdir / "result.json"
            
            df.to_parquet(features_path)
            with open(split_path, 'w') as f:
                json.dump(split_config, f)
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Run
            args = argparse.Namespace(
                features_path=str(features_path),
                split_config_path=str(split_path),
                model_path=str(model_path),
                output_path=str(output_path),
                n_permutations=20, # Small for speed
                random_state=42
            )
            
            result = run_permutation_test(args)
            
            # Verify output
            assert os.path.exists(output_path)
            assert 'p_value_permutation' in result
            assert 0.0 <= result['p_value_permutation'] <= 1.0

def test_parse_args():
    """Test argument parsing."""
    args = parse_args()
    assert args.n_permutations == 1000
    assert args.random_state == 42