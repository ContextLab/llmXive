import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions from the module
from model_training import (
    log_cv_metrics,
    aggregate_cv_metrics,
    run_cross_validation,
    setup_stratified_kfold,
    set_class_weights,
    train_random_forest,
    get_memory_usage_mb,
    check_memory_pressure,
    profile_memory_usage,
    force_gc,
    load_feature_matrix,
    calculate_permutation_importance,
    rank_traits,
    save_model,
    load_model,
    save_importance_results,
    run_training_pipeline
)
from config import get_results_root

class TestCVLogging:
    """Tests for T027: Logging Setup"""

    def test_log_cv_metrics_creates_file(self, tmp_path):
        """Verify log_cv_metrics creates results/metrics.json with correct keys."""
        metrics = {
            "auc_mean": 0.85,
            "auc_std": 0.05,
            "precision_mean": 0.80,
            "recall_mean": 0.75,
            "n_folds": 5,
            "fold_details": []
        }
        output_file = tmp_path / "metrics.json"

        result_path = log_cv_metrics(metrics, output_path=str(output_file))

        assert result_path == str(output_file)
        assert output_file.exists()

        with open(output_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["auc_mean"] == 0.85
        assert saved_data["auc_std"] == 0.05
        assert saved_data["precision_mean"] == 0.80
        assert saved_data["recall_mean"] == 0.75

    def test_log_cv_metrics_missing_keys_raises(self):
        """Verify log_cv_metrics raises error if required keys are missing."""
        incomplete_metrics = {
            "auc_mean": 0.85,
            "precision_mean": 0.80
            # Missing auc_std and recall_mean
        }
        with pytest.raises(ValueError, match="Missing required metric keys"):
            log_cv_metrics(incomplete_metrics, output_path="/tmp/test.json")

class TestCrossValidation:
    """Tests for T029: Cross-Validation Loop"""

    def test_run_cross_validation_structure(self):
        """Test that CV returns correct structure."""
        # Create small dummy data
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)

        cv = setup_stratified_kfold(n_splits=3)
        scores, details = run_cross_validation(X, y, cv=cv, random_state=42)

        assert len(scores) == 3
        assert len(details) == 3
        assert isinstance(scores[0], float)
        for d in details:
            assert "fold" in d
            assert "auc" in d
            assert "precision" in d
            assert "recall" in d

    def test_aggregate_cv_metrics(self):
        """Test aggregation logic."""
        scores = [0.8, 0.9, 0.85]
        details = [
            {"precision": 0.8, "recall": 0.7},
            {"precision": 0.9, "recall": 0.8},
            {"precision": 0.85, "recall": 0.75}
        ]

        metrics = aggregate_cv_metrics(scores, details)

        assert abs(metrics["auc_mean"] - 0.85) < 0.001
        assert "auc_std" in metrics
        assert abs(metrics["precision_mean"] - 0.85) < 0.001
        assert abs(metrics["recall_mean"] - 0.75) < 0.001
        assert metrics["n_folds"] == 3

class TestMemoryProfiling:
    """Tests for T026b: Memory Profiling"""

    def test_get_memory_usage_mb(self):
        """Test memory usage function runs without error."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, float)
        assert usage >= 0

    def test_check_memory_pressure(self):
        """Test pressure check function."""
        # Should return boolean
        result = check_memory_pressure(threshold_mb=1000000) # High threshold
        assert isinstance(result, bool)

    def test_profile_memory_usage_decorator(self):
        """Test decorator adds logging."""
        @profile_memory_usage
        def dummy_func():
            return 42

        result = dummy_func()
        assert result == 42

class TestModelTraining:
    """Tests for T028/T029/T030: Model Training Components"""

    def test_set_class_weights(self):
        """Test class weight calculation."""
        y = np.array([0, 0, 0, 1, 1])
        weights = set_class_weights(y)
        assert 0 in weights
        assert 1 in weights
        # Class 0 has 3 samples, Class 1 has 2. Weight should be inverse proportional
        # Total 5. W0 = 5/(2*3) = 0.833, W1 = 5/(2*2) = 1.25
        assert abs(weights[0] - 0.833) < 0.01
        assert abs(weights[1] - 1.25) < 0.01

    def test_train_random_forest(self):
        """Test model training."""
        X = np.random.rand(50, 3)
        y = np.random.randint(0, 2, 50)
        weights = {0: 1.0, 1: 1.0}

        model = train_random_forest(X, y, weights, random_state=42)
        assert model is not None
        assert hasattr(model, 'predict')

    def test_rank_traits(self):
        """Test trait ranking."""
        importance = np.array([0.1, 0.5, 0.3])
        names = ["A", "B", "C"]

        ranked = rank_traits(importance, names, top_n=2)

        assert len(ranked) == 2
        assert ranked[0]["feature"] == "B"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["feature"] == "C"
        assert ranked[1]["rank"] == 2

class TestModelSerialization:
    """Tests for T031: Model Serialization"""

    def test_save_and_load_model(self, tmp_path):
        """Test saving and loading a model."""
        X = np.random.rand(20, 2)
        y = np.random.randint(0, 2, 20)
        weights = {0: 1.0, 1: 1.0}
        model = train_random_forest(X, y, weights)

        path = tmp_path / "test_model.pkl"
        save_model(model, str(path))
        assert path.exists()

        loaded = load_model(str(path))
        assert loaded is not None
        # Verify predictions match
        pred_orig = model.predict(X)
        pred_load = loaded.predict(X)
        assert np.array_equal(pred_orig, pred_load)

    def test_save_importance_results(self, tmp_path):
        """Test saving importance results."""
        data = [{"rank": 1, "feature": "A", "importance": 0.5}]
        path = tmp_path / "importance.json"
        save_importance_results(data, str(path))
        assert path.exists()
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data