"""
Unit tests for evaluate_static module.
"""

import pytest
import os
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Add code directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.evaluate_static import (
    load_merged_dataset,
    load_model,
    prepare_features_and_labels,
    evaluate_model,
    find_model_files,
    main
)


class TestLoadMergedDataset:
    """Tests for load_merged_dataset function."""

    def test_load_valid_dataset(self, tmp_path):
        """Test loading a valid merged dataset."""
        # Create a temporary CSV file
        csv_path = tmp_path / "merged_dataset.csv"
        data = {
            'document_id': [1, 2, 3],
            'token_id': [10, 20, 30],
            'features': ['[0.1, 0.2]', '[0.3, 0.4]', '[0.5, 0.6]'],
            'rtpurbo_label': [0, 1, 0]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Load and verify
        loaded_df = load_merged_dataset(str(csv_path))
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['document_id', 'token_id', 'features', 'rtpurbo_label']

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent_path = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_merged_dataset(str(non_existent_path))

    def test_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        csv_path = tmp_path / "incomplete.csv"
        data = {
            'document_id': [1, 2],
            'token_id': [10, 20]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError):
            load_merged_dataset(str(csv_path))


class TestLoadModel:
    """Tests for load_model function."""

    def test_load_valid_model(self, tmp_path):
        """Test loading a valid model."""
        model_path = tmp_path / "model_seed_42.pkl"
        model = DecisionTreeClassifier(max_depth=2, random_state=42)
        joblib.dump(model, model_path)

        loaded_model = load_model(str(model_path))
        assert isinstance(loaded_model, DecisionTreeClassifier)

    def test_missing_model_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing model file."""
        non_existent_path = tmp_path / "non_existent.pkl"
        with pytest.raises(FileNotFoundError):
            load_model(str(non_existent_path))


class TestPrepareFeaturesAndLabels:
    """Tests for prepare_features_and_labels function."""

    def test_prepare_features_correct_split(self):
        """Test that features are correctly split into train/test."""
        # Create sample data
        data = {
            'features': ['[0.1, 0.2]', '[0.3, 0.4]', '[0.5, 0.6]', '[0.7, 0.8]',
                         '[0.9, 1.0]', '[1.1, 1.2]', '[1.3, 1.4]', '[1.5, 1.6]'],
            'rtpurbo_label': [0, 1, 0, 1, 0, 1, 0, 1]
        }
        df = pd.DataFrame(data)

        X_train, y_train, X_test, y_test = prepare_features_and_labels(df, seed=42)

        # With 8 samples and 0.2 test ratio, test set should have ~1-2 samples
        assert len(X_test) > 0
        assert len(X_train) > 0
        assert len(X_train) + len(X_test) == 8

        # Check feature shapes
        assert X_train.shape[1] == 2
        assert X_test.shape[1] == 2

    def test_feature_parsing_various_formats(self):
        """Test parsing of various feature formats."""
        data = {
            'features': ['[1.0, 2.0, 3.0]', '[4.0, 5.0, 6.0]', '[7.0, 8.0, 9.0]'],
            'rtpurbo_label': [0, 1, 0]
        }
        df = pd.DataFrame(data)

        X_train, y_train, X_test, y_test = prepare_features_and_labels(df, seed=42)

        # All features should be parsed correctly
        assert X_train.shape[1] == 3 or X_test.shape[1] == 3


class TestEvaluateModel:
    """Tests for evaluate_model function."""

    def test_evaluate_model_metrics(self):
        """Test that evaluation returns correct metrics."""
        # Create a simple model and test data
        X_train = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]])
        y_train = np.array([0, 1, 0, 1])

        model = DecisionTreeClassifier(max_depth=2, random_state=42)
        model.fit(X_train, y_train)

        X_test = np.array([[0.2, 0.3], [0.6, 0.7]])
        y_test = np.array([0, 1])

        metrics = evaluate_model(model, X_test, y_test)

        # Check that all expected keys are present
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'accuracy' in metrics
        assert 'f1' in metrics
        assert 'n_samples' in metrics

        # Check that metrics are floats
        assert isinstance(metrics['precision'], float)
        assert isinstance(metrics['recall'], float)
        assert isinstance(metrics['accuracy'], float)
        assert isinstance(metrics['f1'], float)

    def test_empty_test_set(self):
        """Test evaluation with empty test set."""
        model = DecisionTreeClassifier()
        X_test = np.array([]).reshape(0, 2)
        y_test = np.array([])

        metrics = evaluate_model(model, X_test, y_test)

        assert metrics['n_samples'] == 0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0


class TestFindModelFiles:
    """Tests for find_model_files function."""

    def test_find_all_model_files(self, tmp_path):
        """Test finding all model files in directory."""
        # Create some model files
        (tmp_path / "model_seed_42.pkl").touch()
        (tmp_path / "model_seed_123.pkl").touch()
        (tmp_path / "other_file.txt").touch()
        (tmp_path / "model_seed_999.pkl").touch()

        model_files = find_model_files(str(tmp_path))

        assert len(model_files) == 3
        assert all(f.endswith('.pkl') for f in model_files)
        assert all('model_seed_' in f for f in model_files)

    def test_empty_directory(self, tmp_path):
        """Test finding models in empty directory."""
        model_files = find_model_files(str(tmp_path))
        assert len(model_files) == 0

    def test_missing_directory(self, tmp_path):
        """Test that FileNotFoundError is raised for missing directory."""
        non_existent_path = tmp_path / "non_existent_dir"
        with pytest.raises(FileNotFoundError):
            find_model_files(str(non_existent_path))


class TestMain:
    """Tests for main function."""

    def test_main_execution(self, tmp_path):
        """Test full execution of main function."""
        # Create temporary directories and files
        data_dir = tmp_path / "data" / "intermediate"
        models_dir = tmp_path / "data" / "intermediate" / "models"
        data_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)

        # Create merged dataset
        csv_path = data_dir / "merged_dataset.csv"
        data = {
            'document_id': list(range(20)),
            'token_id': list(range(20)),
            'features': ['[0.1, 0.2]'] * 20,
            'rtpurbo_label': [0, 1] * 10
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Create trained models
        for seed in [42, 123, 999]:
            model = DecisionTreeClassifier(max_depth=2, random_state=seed)
            model.fit(np.random.rand(10, 2), [0, 1] * 5)
            joblib.dump(model, models_dir / f"model_seed_{seed}.pkl")

        # Run main
        output_path = tmp_path / "data" / "intermediate" / "static_eval_scores.json"
        args = type('Args', (), {
            'merged_dataset': str(csv_path),
            'models_dir': str(models_dir),
            'output': str(output_path),
            'test_split_ratio': 0.2,
            'seed': 42
        })()

        results = main(args)

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 3  # 3 models

        # Verify output file was created
        assert output_path.exists()
        with open(output_path) as f:
            saved_results = json.load(f)
        assert len(saved_results) == 3

        # Verify each result has required keys
        for result in saved_results:
            assert 'seed' in result
            assert 'precision' in result
            assert 'recall' in result
            assert 'accuracy' in result
            assert 'f1' in result