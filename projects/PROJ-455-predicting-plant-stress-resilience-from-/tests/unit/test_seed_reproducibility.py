"""Unit tests for seed reproducibility (Constitution Principle I)."""
import os
import json
import numpy as np
import random
import pytest
from data.generator import generate_synthetic_data
from models.train import train_random_forest
from main import run_pipeline, parse_args

class TestSeedReproducibility:
    """Tests that verify seed-based reproducibility."""
    
    def test_generator_deterministic_with_seed(self, tmp_path):
        """Test that generate_synthetic_data produces identical results with same seed."""
        # Change to temp directory for clean test
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create data directory
            os.makedirs("data/raw", exist_ok=True)
            
            seed = 123
            path1 = generate_synthetic_data(n_samples=50, stress_type="drought", seed=seed)
            path2 = generate_synthetic_data(n_samples=50, stress_type="drought", seed=seed)
            
            # Both runs should produce identical files
            import pandas as pd
            df1 = pd.read_parquet(path1)
            df2 = pd.read_parquet(path2)
            
            assert df1.equals(df2), "Synthetic data should be identical with same seed"
        finally:
            os.chdir(original_cwd)
    
    def test_pipeline_seed_propagation(self, tmp_path):
        """Test that --seed argument propagates to all random operations."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create necessary directories
            os.makedirs("data/raw", exist_ok=True)
            os.makedirs("data/results", exist_ok=True)
            
            seed = 456
            args = parse_args()
            args.seed = seed
            args.n_samples = 30
            args.stress_type = "drought"
            args.missing_rate = 0.05
            
            # Run pipeline twice
            results1 = run_pipeline(args)
            
            # Reset random state and run again
            np.random.seed(seed)
            random.seed(seed)
            results2 = run_pipeline(args)
            
            # Results should be identical
            assert results1["models"]["random_forest"]["metric_value"] == results2["models"]["random_forest"]["metric_value"]
            assert results1["models"]["random_forest"]["seed_used"] == seed
        finally:
            os.chdir(original_cwd)
    
    def test_model_training_reproducibility(self):
        """Test that model training is reproducible with same seed."""
        # Generate test data
        np.random.seed(42)
        X = np.random.randn(50, 5)
        y = np.random.randn(50)
        
        # Train twice with same seed
        model1, metrics1 = train_random_forest(X, y, cv=3, seed=999)
        model2, metrics2 = train_random_forest(X, y, cv=3, seed=999)
        
        # Predictions should be identical
        pred1 = model1.predict(X)
        pred2 = model2.predict(X)
        
        np.testing.assert_array_almost_equal(pred1, pred2)
        assert metrics1["metric_value"] == metrics2["metric_value"]
    
    def test_results_file_contains_seed(self, tmp_path):
        """Test that results file explicitly records the seed used."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            os.makedirs("data/raw", exist_ok=True)
            os.makedirs("data/results", exist_ok=True)
            
            seed = 789
            args = parse_args()
            args.seed = seed
            args.n_samples = 20
            args.stress_type = "drought"
            args.missing_rate = 0.05
            
            run_pipeline(args)
            
            # Check results file
            results_path = "data/results/model_metrics.json"
            assert os.path.exists(results_path)
            
            with open(results_path, "r") as f:
                results = json.load(f)
            
            assert results["seed"] == seed
            assert results["models"]["random_forest"]["seed_used"] == seed
            assert results["models"]["svm"]["seed_used"] == seed
        finally:
            os.chdir(original_cwd)