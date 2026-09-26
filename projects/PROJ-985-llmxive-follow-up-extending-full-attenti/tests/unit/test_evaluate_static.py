"""
Unit tests for evaluate_static.py module.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
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


class TestEvaluateStatic:
    """Test cases for evaluate_static module."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_merged_dataset(self, temp_dir):
        """Create a sample merged dataset CSV."""
        data = {
            'entropy': [0.5, 0.8, 0.3, 0.9, 0.6],
            'pos_tag': [1, 2, 1, 3, 2],
            'position': [10, 20, 30, 40, 50],
            'kenlm_perplexity': [1.2, 1.5, 0.9, 1.8, 1.3],
            'local_semantic_density': [0.4, 0.6, 0.3, 0.7, 0.5],
            'rtpurbo_label': [1, 0, 1, 0, 1]
        }
        df = pd.DataFrame(data)
        csv_path = temp_dir / "merged_dataset.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def sample_models(self, temp_dir):
        """Create sample model files."""
        models_dir = temp_dir / "models" / "seeds"
        models_dir.mkdir(parents=True)
        
        # Create dummy models (simple objects with predict method)
        class DummyModel:
            def predict(self, X):
                return np.random.randint(0, 2, size=X.shape[0])
        
        seeds = [42, 123, 456]
        model_paths = []
        for seed in seeds:
            model_path = models_dir / f"model_seed_{seed}.pkl"
            import pickle
            with open(model_path, 'wb') as f:
                pickle.dump(DummyModel(), f)
            model_paths.append(model_path)
        
        return models_dir, seeds

    def test_prepare_features_and_labels(self, sample_merged_dataset):
        """Test feature and label preparation."""
        df = pd.read_csv(sample_merged_dataset)
        feature_cols = ['entropy', 'pos_tag', 'position', 'kenlm_perplexity', 'local_semantic_density']
        
        X, y = prepare_features_and_labels(df, feature_cols, label_col='rtpurbo_label')
        
        assert X.shape == (5, 5), f"Expected X shape (5, 5), got {X.shape}"
        assert y.shape == (5,), f"Expected y shape (5,), got {y.shape}"
        assert y.dtype == int, f"Expected y dtype int, got {y.dtype}"

    def test_evaluate_model(self, temp_dir):
        """Test model evaluation with dummy data."""
        # Create dummy model
        class DummyModel:
            def __init__(self):
                self.predictions = [1, 0, 1, 0, 1]
            
            def predict(self, X):
                return np.array(self.predictions)
        
        model = DummyModel()
        X_test = np.random.rand(5, 3)
        y_test = np.array([1, 0, 1, 0, 1])
        
        metrics = evaluate_model(model, X_test, y_test)
        
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert isinstance(metrics['precision'], float)
        assert isinstance(metrics['recall'], float)
        assert 0 <= metrics['precision'] <= 1
        assert 0 <= metrics['recall'] <= 1

    def test_evaluate_model_zero_division(self, temp_dir):
        """Test evaluation handles zero division correctly."""
        # Create model that predicts all zeros
        class ZeroPredictor:
            def predict(self, X):
                return np.zeros(X.shape[0], dtype=int)
        
        model = ZeroPredictor()
        X_test = np.random.rand(5, 3)
        y_test = np.array([1, 1, 1, 1, 1])  # All positive, but model predicts all negative
        
        metrics = evaluate_model(model, X_test, y_test)
        
        # Precision and recall should be 0 when TP=0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0

    def test_find_model_files(self, sample_models):
        """Test finding model files."""
        models_dir, expected_seeds = sample_models
        
        # Mock the SEEDS_DIR to point to our temp directory
        with patch('models.evaluate_static.SEEDS_DIR', models_dir):
            model_files = find_model_files()
            
            assert len(model_files) == len(expected_seeds)
            seed_ids = [m['seed_id'] for m in model_files]
            assert set(seed_ids) == set(expected_seeds)

    def test_find_model_files_no_models(self, temp_dir):
        """Test finding model files when none exist."""
        models_dir = temp_dir / "models" / "seeds"
        models_dir.mkdir(parents=True)
        
        with patch('models.evaluate_static.SEEDS_DIR', models_dir):
            with pytest.raises(FileNotFoundError):
                find_model_files()

    @patch('models.evaluate_static.load_merged_dataset')
    @patch('models.evaluate_static.find_model_files')
    @patch('models.evaluate_static.load_model')
    @patch('models.evaluate_static.evaluate_model')
    @patch('models.evaluate_static.INTERMEDIATE_DIR')
    def test_main_success(self, mock_intermediate_dir, mock_evaluate, mock_load_model, 
                          mock_find_models, mock_load_dataset, temp_dir):
        """Test main function successful execution."""
        # Setup mocks
        mock_intermediate_dir.__truediv__ = lambda self, name: temp_dir / name
        mock_intermediate_dir.mkdir = MagicMock()
        
        mock_load_dataset.return_value = pd.DataFrame({
            'entropy': [0.5],
            'pos_tag': [1],
            'position': [10],
            'kenlm_perplexity': [1.2],
            'local_semantic_density': [0.4],
            'rtpurbo_label': [1]
        })
        
        mock_find_models.return_value = [
            {'seed_id': 42, 'model_path': temp_dir / 'model.pkl'}
        ]
        
        mock_load_model.return_value = MagicMock()
        mock_load_model.return_value.predict.return_value = np.array([1])
        
        mock_evaluate.return_value = {'precision': 0.8, 'recall': 0.9}
        
        # Run main
        result = main()
        
        assert result == 0
        
        # Verify output file was created
        output_file = temp_dir / "static_eval_scores.json"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['seed_id'] == 42
        assert 'precision' in data[0]
        assert 'recall' in data[0]

    @patch('models.evaluate_static.load_merged_dataset')
    def test_main_missing_dataset(self, mock_load_dataset, temp_dir):
        """Test main function when dataset is missing."""
        mock_load_dataset.side_effect = FileNotFoundError("Dataset not found")
        
        result = main()
        
        assert result == 1