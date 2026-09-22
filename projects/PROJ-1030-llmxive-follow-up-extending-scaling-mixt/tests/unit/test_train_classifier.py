"""
Unit tests for classifier training logic in code/train_classifier.py.

This module tests the core logic of the classifier training pipeline,
including data loading, preprocessing, model training, and evaluation.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from train_classifier import (
    load_data,
    preprocess_data,
    train_model,
    evaluate_model,
    compute_baseline_f1,
    compute_feature_importance,
    save_metrics,
    save_activation_distribution,
    main
)

# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_features(temp_data_dir):
    """Create sample features.npy file."""
    # Create sample features: 100 samples, 50 features
    features = np.random.randn(100, 50).astype(np.float32)
    features_path = Path(temp_data_dir) / "features.npy"
    np.save(features_path, features)
    return features_path

@pytest.fixture
def sample_labels(temp_data_dir):
    """Create sample labels.csv file with valid, invalid, and null labels."""
    labels_data = {
        'clip_id': [f"clip_{i:03d}" for i in range(100)],
        'label': ['valid'] * 40 + ['invalid'] * 40 + ['null'] * 20,
        'reason': ['gravity'] * 20 + ['collision'] * 20 + ['none'] * 40 + ['low_confidence'] * 20,
        'confidence_score': [0.95] * 40 + [0.85] * 40 + [0.5] * 20,
        'perturbation_type': [0] * 80 + [1] * 20
    }
    labels_df = pd.DataFrame(labels_data)
    labels_path = Path(temp_data_dir) / "labels.csv"
    labels_df.to_csv(labels_path, index=False)
    return labels_path

@pytest.fixture
def sample_metadata(temp_data_dir):
    """Create sample metadata.json file."""
    metadata = {
        'model_name': 'test_model',
        'extraction_date': '2024-01-01',
        'num_samples': 100
    }
    metadata_path = Path(temp_data_dir) / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    return metadata_path

# ========================================================================
# Test Data Loading
# ========================================================================

class TestLoadData:
    """Tests for the load_data function."""
    
    def test_load_data_success(self, sample_features, sample_labels):
        """Test successful loading of features and labels."""
        features, labels_df, metadata = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=sample_features.parent / "metadata.json"
        )
        
        assert isinstance(features, np.ndarray)
        assert features.shape[0] == 100
        assert isinstance(labels_df, pd.DataFrame)
        assert len(labels_df) == 100
        assert 'label' in labels_df.columns
        assert 'clip_id' in labels_df.columns
    
    def test_load_data_missing_metadata(self, sample_features, sample_labels):
        """Test loading when metadata file is missing."""
        features, labels_df, metadata = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=sample_features.parent / "nonexistent.json"
        )
        
        assert isinstance(features, np.ndarray)
        assert isinstance(labels_df, pd.DataFrame)
        assert metadata is None
    
    def test_load_data_invalid_features(self, temp_data_dir, sample_labels):
        """Test loading with invalid features file."""
        invalid_features = Path(temp_data_dir) / "invalid.npy"
        invalid_features.write_text("not a numpy file")
        
        with pytest.raises(Exception):
            load_data(
                features_path=invalid_features,
                labels_path=sample_labels,
                metadata_path=None
            )
    
    def test_load_data_invalid_labels(self, sample_features, temp_data_dir):
        """Test loading with invalid labels file."""
        invalid_labels = Path(temp_data_dir) / "invalid.csv"
        invalid_labels.write_text("not a csv file")
        
        with pytest.raises(Exception):
            load_data(
                features_path=sample_features,
                labels_path=invalid_labels,
                metadata_path=None
            )

# ========================================================================
# Test Data Preprocessing
# ========================================================================

class TestPreprocessData:
    """Tests for the preprocess_data function."""
    
    def test_preprocess_data_filter_nulls(self, sample_features, sample_labels):
        """Test that null labels are filtered out."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, train_indices, test_indices = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        # Check that null labels are excluded
        assert len(y_train) + len(y_test) == 80  # 100 - 20 nulls
        assert all(label in ['valid', 'invalid'] for label in y_train)
        assert all(label in ['valid', 'invalid'] for label in y_test)
    
    def test_preprocess_data_train_test_split(self, sample_features, sample_labels):
        """Test that data is split into train and test sets."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, train_indices, test_indices = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        # Check split sizes (80% train, 20% test of 80 non-null samples)
        assert len(X_train) == 64  # 80 * 0.8
        assert len(X_test) == 16   # 80 * 0.2
        assert len(y_train) == 64
        assert len(y_test) == 16
        
        # Check feature dimensions
        assert X_train.shape[1] == 50
        assert X_test.shape[1] == 50
    
    def test_preprocess_data_imbalanced_classes(self, temp_data_dir, sample_features):
        """Test preprocessing with imbalanced class distribution."""
        # Create labels with imbalanced classes
        labels_data = {
            'clip_id': [f"clip_{i:03d}" for i in range(100)],
            'label': ['valid'] * 90 + ['invalid'] * 10,
            'reason': ['none'] * 90 + ['gravity'] * 10,
            'confidence_score': [0.95] * 100,
            'perturbation_type': [0] * 100
        }
        labels_df = pd.DataFrame(labels_data)
        labels_path = Path(temp_data_dir) / "labels_imbalanced.csv"
        labels_df.to_csv(labels_path, index=False)
        
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=labels_path,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, train_indices, test_indices = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        # Check that imbalanced data is handled
        assert len(X_train) > 0
        assert len(X_test) > 0
        assert len(y_train) > 0
        assert len(y_test) > 0

# ========================================================================
# Test Model Training
# ========================================================================

class TestTrainModel:
    """Tests for the train_model function."""
    
    def test_train_model_mlp(self, sample_features, sample_labels):
        """Test training MLP model."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, train_history = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='mlp',
            hidden_units=[64, 32],
            learning_rate=0.001,
            epochs=5,
            batch_size=32
        )
        
        assert model is not None
        assert 'loss' in train_history
        assert 'accuracy' in train_history
        assert len(train_history['loss']) == 5
    
    def test_train_model_random_forest(self, sample_features, sample_labels):
        """Test training Random Forest model."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, train_history = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='random_forest',
            n_estimators=10,
            max_depth=5
        )
        
        assert model is not None
        assert 'train_accuracy' in train_history
        assert 'train_f1' in train_history
    
    def test_train_model_invalid_type(self, sample_features, sample_labels):
        """Test training with invalid model type."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        with pytest.raises(ValueError):
            train_model(
                X_train=X_train,
                y_train=y_train,
                model_type='invalid_model'
            )

# ========================================================================
# Test Model Evaluation
# ========================================================================

class TestEvaluateModel:
    """Tests for the evaluate_model function."""
    
    def test_evaluate_model_metrics(self, sample_features, sample_labels):
        """Test evaluation returns correct metrics."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        # Train a simple model
        model, _ = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='random_forest',
            n_estimators=5
        )
        
        metrics = evaluate_model(model, X_test, y_test)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 'confusion_matrix' in metrics
        
        # Check metric ranges
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['precision'] <= 1
        assert 0 <= metrics['recall'] <= 1
        assert 0 <= metrics['f1_score'] <= 1
    
    def test_evaluate_model_confusion_matrix(self, sample_features, sample_labels):
        """Test confusion matrix has correct shape."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, _ = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='random_forest',
            n_estimators=5
        )
        
        metrics = evaluate_model(model, X_test, y_test)
        
        cm = metrics['confusion_matrix']
        assert cm.shape == (2, 2)  # Binary classification

# ========================================================================
# Test Baseline Computation
# ========================================================================

class TestComputeBaselineF1:
    """Tests for the compute_baseline_f1 function."""
    
    def test_compute_baseline_majority_class(self, sample_features, sample_labels):
        """Test baseline F1 for majority class predictor."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        baseline_f1 = compute_baseline_f1(y_train, y_test)
        
        assert isinstance(baseline_f1, float)
        assert 0 <= baseline_f1 <= 1
        
        # With balanced classes (40 valid, 40 invalid), baseline should be around 0.5
        # (since we have equal numbers, majority class predictor gets ~50% accuracy)
        assert baseline_f1 < 1.0  # Should not be perfect

# ========================================================================
# Test Feature Importance
# ========================================================================

class TestComputeFeatureImportance:
    """Tests for the compute_feature_importance function."""
    
    def test_compute_feature_importance_rf(self, sample_features, sample_labels):
        """Test feature importance for Random Forest."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, _ = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='random_forest',
            n_estimators=5
        )
        
        importance = compute_feature_importance(model, X_train, y_train)
        
        assert isinstance(importance, dict)
        assert 'feature_importance' in importance
        assert 'top_features' in importance
        
        # Check feature importance array
        assert len(importance['feature_importance']) == 50
        assert all(imp >= 0 for imp in importance['feature_importance'])
        
        # Check top features
        assert len(importance['top_features']) <= 50
        assert all(isinstance(f, dict) for f in importance['top_features'])
    
    def test_compute_feature_importance_mlp(self, sample_features, sample_labels):
        """Test feature importance for MLP (should use permutation importance)."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, _ = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='mlp',
            hidden_units=[32, 16],
            epochs=3
        )
        
        importance = compute_feature_importance(model, X_train, y_train)
        
        assert isinstance(importance, dict)
        assert 'feature_importance' in importance
        assert len(importance['feature_importance']) == 50

# ========================================================================
# Test Activation Distribution
# ========================================================================

class TestSaveActivationDistribution:
    """Tests for the save_activation_distribution function."""
    
    def test_save_activation_distribution(self, sample_features, temp_data_dir):
        """Test saving activation distribution."""
        features = np.load(sample_features)
        
        output_path = Path(temp_data_dir) / "activation_distribution.json"
        save_activation_distribution(features, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            distribution = json.load(f)
        
        assert 'mean' in distribution
        assert 'std' in distribution
        assert 'histogram' in distribution
        assert 'expert_mask_counts' in distribution
        
        # Check types
        assert isinstance(distribution['mean'], float)
        assert isinstance(distribution['std'], float)
        assert isinstance(distribution['histogram'], list)
        assert isinstance(distribution['expert_mask_counts'], dict)

# ========================================================================
# Test Metrics Saving
# ========================================================================

class TestSaveMetrics:
    """Tests for the save_metrics function."""
    
    def test_save_metrics(self, temp_data_dir):
        """Test saving metrics to JSON."""
        metrics = {
            'accuracy': 0.85,
            'precision': 0.82,
            'recall': 0.88,
            'f1_score': 0.85,
            'baseline_f1': 0.50,
            'model_type': 'random_forest'
        }
        
        output_path = Path(temp_data_dir) / "metrics.json"
        save_metrics(metrics, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_metrics = json.load(f)
        
        assert saved_metrics == metrics

# ========================================================================
# Test Main Function
# ========================================================================

class TestMain:
    """Tests for the main function."""
    
    def test_main_full_pipeline(self, temp_data_dir, sample_features, sample_labels):
        """Test running the full training pipeline."""
        # Create metadata file
        metadata_path = Path(temp_data_dir) / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({'model_name': 'test'}, f)
        
        # Create output paths
        metrics_path = Path(temp_data_dir) / "metrics.json"
        activation_path = Path(temp_data_dir) / "activation_distribution.json"
        filtering_path = Path(temp_data_dir) / "filtering_report.json"
        
        # Run main
        with patch('sys.argv', [
            'train_classifier.py',
            '--features_path', str(sample_features),
            '--labels_path', str(sample_labels),
            '--metadata_path', str(metadata_path),
            '--metrics_path', str(metrics_path),
            '--activation_path', str(activation_path),
            '--filtering_path', str(filtering_path),
            '--model_type', 'random_forest',
            '--test_size', '0.2',
            '--random_state', '42'
        ]):
            main()
        
        # Check outputs
        assert metrics_path.exists()
        assert activation_path.exists()
        assert filtering_path.exists()
        
        # Verify metrics content
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert 'f1_score' in metrics
        assert 'baseline_f1' in metrics
        assert metrics['f1_score'] >= 0  # Should be a valid F1 score
        
        # Verify activation distribution
        with open(activation_path, 'r') as f:
            distribution = json.load(f)
        
        assert 'mean' in distribution
        assert 'std' in distribution
        
        # Verify filtering report
        with open(filtering_path, 'r') as f:
            report = json.load(f)
        
        assert 'total_samples' in report
        assert 'retained' in report
        assert report['total_samples'] == 100
        assert report['retained'] == 80  # 100 - 20 nulls
    
    def test_main_null_metadata(self, temp_data_dir, sample_features, sample_labels):
        """Test main function with missing metadata."""
        # Create output paths
        metrics_path = Path(temp_data_dir) / "metrics.json"
        activation_path = Path(temp_data_dir) / "activation_distribution.json"
        filtering_path = Path(temp_data_dir) / "filtering_report.json"
        
        # Run main with non-existent metadata path
        with patch('sys.argv', [
            'train_classifier.py',
            '--features_path', str(sample_features),
            '--labels_path', str(sample_labels),
            '--metadata_path', str(Path(temp_data_dir) / "nonexistent.json"),
            '--metrics_path', str(metrics_path),
            '--activation_path', str(activation_path),
            '--filtering_path', str(filtering_path),
            '--model_type', 'mlp',
            '--epochs', '3'
        ]):
            main()
        
        # Should still complete successfully
        assert metrics_path.exists()
        assert activation_path.exists()
        assert filtering_path.exists()

# ========================================================================
# Test Filtering Report Generation
# ========================================================================

class TestFilteringReport:
    """Tests for filtering report generation."""
    
    def test_filtering_report_counts(self, temp_data_dir, sample_features, sample_labels):
        """Test that filtering report correctly counts samples."""
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=sample_labels,
            metadata_path=None
        )
        
        # Count nulls by reason
        null_rows = labels_df[labels_df['label'] == 'null']
        excluded_by_confidence = len(null_rows[null_rows['reason'] == 'low_confidence'])
        excluded_by_simulation = len(null_rows[null_rows['reason'] != 'low_confidence'])
        retained = len(labels_df[labels_df['label'] != 'null'])
        
        assert excluded_by_confidence == 20
        assert excluded_by_simulation == 0
        assert retained == 80

# ========================================================================
# Test Error Handling
# ========================================================================

class TestErrorHandling:
    """Tests for error handling in training pipeline."""
    
    def test_train_with_empty_test_set(self, temp_data_dir, sample_features):
        """Test training when test set would be empty."""
        # Create labels with all nulls
        labels_data = {
            'clip_id': [f"clip_{i:03d}" for i in range(100)],
            'label': ['null'] * 100,
            'reason': ['low_confidence'] * 100,
            'confidence_score': [0.5] * 100,
            'perturbation_type': [0] * 100
        }
        labels_df = pd.DataFrame(labels_data)
        labels_path = Path(temp_data_dir) / "labels_all_null.csv"
        labels_df.to_csv(labels_path, index=False)
        
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=labels_path,
            metadata_path=None
        )
        
        with pytest.raises(ValueError, match="No valid samples"):
            preprocess_data(
                features=features,
                labels_df=labels_df,
                test_size=0.2,
                random_state=42
            )
    
    def test_train_with_single_class(self, temp_data_dir, sample_features):
        """Test training with only one class in data."""
        # Create labels with only one class
        labels_data = {
            'clip_id': [f"clip_{i:03d}" for i in range(100)],
            'label': ['valid'] * 100,
            'reason': ['none'] * 100,
            'confidence_score': [0.95] * 100,
            'perturbation_type': [0] * 100
        }
        labels_df = pd.DataFrame(labels_data)
        labels_path = Path(temp_data_dir) / "labels_single_class.csv"
        labels_df.to_csv(labels_path, index=False)
        
        features, labels_df, _ = load_data(
            features_path=sample_features,
            labels_path=labels_path,
            metadata_path=None
        )
        
        # Should still work but may have warnings
        X_train, X_test, y_train, y_test, _, _ = preprocess_data(
            features=features,
            labels_df=labels_df,
            test_size=0.2,
            random_state=42
        )
        
        model, _ = train_model(
            X_train=X_train,
            y_train=y_train,
            model_type='random_forest',
            n_estimators=5
        )
        
        assert model is not None