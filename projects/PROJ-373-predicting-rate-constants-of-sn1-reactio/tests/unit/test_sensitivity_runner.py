import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from analysis.sensitivity_runner import (
    filter_features_by_variance,
    train_single_model_with_features,
    run_sensitivity_orchestration
)

class TestFilterFeaturesByVariance:
    def test_filter_high_variance(self):
        df = pd.DataFrame({
            'a': [1, 2, 3, 4, 5], # variance > 0
            'b': [1, 1, 1, 1, 1], # variance = 0
            'c': [10, 20, 30, 40, 50] # variance > 0
        })
        cols = ['a', 'b', 'c']
        
        kept = filter_features_by_variance(df, cols, threshold=0.5)
        assert 'a' in kept
        assert 'c' in kept
        assert 'b' not in kept
        assert len(kept) == 2

    def test_filter_all_low_variance(self):
        df = pd.DataFrame({
            'a': [1, 1, 1],
            'b': [2, 2, 2]
        })
        cols = ['a', 'b']
        
        kept = filter_features_by_variance(df, cols, threshold=0.5)
        assert len(kept) == 0

    def test_filter_all_high_variance(self):
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [10, 20, 30]
        })
        cols = ['a', 'b']
        
        kept = filter_features_by_variance(df, cols, threshold=0.5)
        assert len(kept) == 2

class TestTrainSingleModel:
    def test_train_linear(self):
        X = np.array([[1], [2], [3], [4], [5]], dtype=np.float32)
        y = np.array([2, 4, 6, 8, 10], dtype=np.float32)
        
        model, r2, mae = train_single_model_with_features(X, y)
        
        assert r2 == 1.0
        assert mae == 0.0

    def test_train_noisy(self):
        np.random.seed(42)
        X = np.random.rand(100, 5).astype(np.float32)
        y = X[:, 0] + 2 * X[:, 1] + np.random.normal(0, 0.1, 100).astype(np.float32)
        
        model, r2, mae = train_single_model_with_features(X, y)
        
        assert r2 > 0.9 # Should be high correlation
        assert mae < 0.5

class TestRunSensitivityOrchestration:
    def test_orchestration_flow(self):
        # Create a temporary CSV with dummy data
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.csv"
            output_path = Path(tmpdir) / "results.csv"
            
            # Create dummy data
            df = pd.DataFrame({
                'smiles': ['CC', 'CCC', 'CCCC'],
                'rate_constant': [1.0, 2.0, 3.0],
                'feat1': [1.0, 2.0, 3.0],
                'feat2': [1.0, 1.0, 1.0], # low variance
                'feat3': [10.0, 20.0, 30.0]
            })
            df.to_csv(data_path, index=False)
            
            results = run_sensitivity_orchestration(
                model_config=None,
                data_path=data_path,
                output_path=output_path,
                thresholds=[0.5, 2.0]
            )
            
            assert len(results) == 2
            assert output_path.exists()
            
            # Check output file
            out_df = pd.read_csv(output_path)
            assert 'threshold' in out_df.columns
            assert 'r2' in out_df.columns
            assert 'mae' in out_df.columns

    def test_orchestration_empty_features(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.csv"
            output_path = Path(tmpdir) / "results.csv"
            
            # All features have low variance
            df = pd.DataFrame({
                'smiles': ['CC', 'CCC'],
                'rate_constant': [1.0, 2.0],
                'feat1': [1.0, 1.0],
                'feat2': [2.0, 2.0]
            })
            df.to_csv(data_path, index=False)
            
            results = run_sensitivity_orchestration(
                model_config=None,
                data_path=data_path,
                output_path=output_path,
                thresholds=[0.5]
            )
            
            assert len(results) == 1
            assert np.isnan(results[0]['r2'])
            assert np.isnan(results[0]['mae'])