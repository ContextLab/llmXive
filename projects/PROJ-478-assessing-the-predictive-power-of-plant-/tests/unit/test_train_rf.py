"""
Unit tests for src/modeling/train_rf.py

Tests verify:
1. TSS calculation logic
2. Model training with 5-fold CV
3. Output file generation
4. Error handling for missing files
"""
import os
import sys
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.modeling.train_rf import calculate_tss, train_random_forest, run_training_pipeline


class TestTSSCalculation:
    def test_perfect_classification(self):
        """TP=10, TN=10, FP=0, FN=0 -> TSS = 1.0"""
        tss = calculate_tss(10, 10, 0, 0)
        assert abs(tss - 1.0) < 1e-6

    def test_random_classification(self):
        """TP=5, TN=5, FP=5, FN=5 -> Sens=0.5, Spec=0.5 -> TSS = 0.0"""
        tss = calculate_tss(5, 5, 5, 5)
        assert abs(tss - 0.0) < 1e-6

    def test_worst_classification(self):
        """TP=0, TN=0, FP=10, FN=10 -> TSS = -1.0"""
        tss = calculate_tss(0, 0, 10, 10)
        assert abs(tss - (-1.0)) < 1e-6

    def test_zero_division_handling(self):
        """Division by zero should return 0.0"""
        tss = calculate_tss(0, 0, 0, 0)
        assert tss == 0.0


class TestRandomForestTraining:
    def test_training_produces_metrics(self):
        """Verify training returns expected metrics dict"""
        # Generate dummy data
        np.random.seed(42)
        X = np.random.rand(100, 3)
        y = np.random.randint(0, 2, 100)
        
        model, metrics = train_random_forest(X, y, n_splits=3)
        
        assert model is not None
        assert "auc" in metrics
        assert "tss" in metrics
        assert "threshold" in metrics
        assert metrics["n_splits"] == 3
        assert metrics["max_depth"] == 10 # From config
        assert metrics["n_estimators"] == 100 # From config

    def test_auc_range(self):
        """AUC should be between 0 and 1"""
        np.random.seed(42)
        X = np.random.rand(200, 3)
        y = np.random.randint(0, 2, 200)
        
        _, metrics = train_random_forest(X, y, n_splits=3)
        assert 0.0 <= metrics["auc"] <= 1.0


class TestPipelineIntegration:
    def test_run_training_pipeline_creates_files(self):
        """Verify pipeline creates model and metrics files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy input data
            input_path = Path(tmpdir) / "input.csv"
            model_path = Path(tmpdir) / "model.joblib"
            metrics_path = Path(tmpdir) / "metrics.json"
            
            df = pd.DataFrame({
                "presence": [1, 0, 1, 0, 1, 0, 1, 0] * 10,
                "bio1": np.random.rand(80),
                "bio12": np.random.rand(80)
            })
            df.to_csv(input_path, index=False)
            
            run_training_pipeline(
                input_data_path=str(input_path),
                output_model_path=str(model_path),
                output_metrics_path=str(metrics_path)
            )
            
            assert model_path.exists()
            assert metrics_path.exists()
            
            with open(metrics_path) as f:
                metrics = json.load(f)
            assert "auc" in metrics
            assert "tss" in metrics

    def test_missing_input_file_raises_error(self):
        """Verify FileNotFoundError is raised for missing input"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                run_training_pipeline(
                    input_data_path=str(Path(tmpdir) / "nonexistent.csv"),
                    output_model_path=str(Path(tmpdir) / "model.joblib"),
                    output_metrics_path=str(Path(tmpdir) / "metrics.json")
                )
