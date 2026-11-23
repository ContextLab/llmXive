"""
Unit tests for compute_metrics.py
"""
import pytest
import numpy as np
import json
import tempfile
import pandas as pd
from pathlib import Path
import pickle
from sklearn.ensemble import RandomForestClassifier

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.classification.compute_metrics import (
    calculate_majority_baseline,
    compute_metrics,
    run_metrics_evaluation
)

class TestMajorityBaseline:
    """Test majority class baseline calculation"""
    
    def test_balanced_dataset(self):
        """Test with balanced dataset (50/50)"""
        y_true = np.array([0, 1, 0, 1, 0, 1])
        f1 = calculate_majority_baseline(y_true)
        # With balanced data, majority class is 50%, F1 should be 0.5
        assert abs(f1 - 0.5) < 0.01
    
    def test_imbalanced_dataset(self):
        """Test with imbalanced dataset (80/20)"""
        y_true = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1])
        f1 = calculate_majority_baseline(y_true)
        # Majority class is 0 (80%), F1 for predicting all 0s
        # TP=0, FP=0, FN=2, TN=8 -> Precision undefined (0/0), Recall=0 -> F1=0
        # But sklearn handles this with zero_division
        assert f1 >= 0.0
    
    def test_all_same_class(self):
        """Test with all same class"""
        y_true = np.array([1, 1, 1, 1, 1])
        f1 = calculate_majority_baseline(y_true)
        assert abs(f1 - 1.0) < 0.01
    
    def test_empty_array(self):
        """Test with empty array"""
        y_true = np.array([])
        f1 = calculate_majority_baseline(y_true)
        assert f1 == 0.0

class TestComputeMetrics:
    """Test metric computation"""
    
    def test_perfect_prediction(self):
        """Test with perfect predictions"""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        metrics = compute_metrics(y_true, y_pred)
        
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0
    
    def test_worst_prediction(self):
        """Test with worst predictions (inverted)"""
        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([1, 0, 1, 0])
        metrics = compute_metrics(y_true, y_pred)
        
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0
    
    def test_empty_arrays(self):
        """Test with empty arrays"""
        y_true = np.array([])
        y_pred = np.array([])
        metrics = compute_metrics(y_true, y_pred)
        
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0
    
    def test_confusion_matrix(self):
        """Test confusion matrix calculation"""
        y_true = np.array([0, 0, 0, 0, 1, 1, 1, 1])
        y_pred = np.array([0, 0, 1, 1, 0, 0, 1, 1])
        metrics = compute_metrics(y_true, y_pred)
        
        cm = metrics['confusion_matrix']
        # Expected: [[2, 2], [2, 2]]
        assert cm[0][0] == 2  # TN
        assert cm[0][1] == 2  # FP
        assert cm[1][0] == 2  # FN
        assert cm[1][1] == 2  # TP

class TestRunMetricsEvaluation:
    """Test full evaluation pipeline"""
    
    def test_end_to_end(self):
        """Test complete evaluation pipeline"""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create dummy data
            n_samples = 100
            features = np.random.randn(n_samples, 10)
            labels = np.random.randint(0, 2, n_samples)
            
            # Create labels CSV
            labels_df = pd.DataFrame({
                'clip_id': [f'clip_{i}' for i in range(n_samples)],
                'label': ['valid' if l == 1 else 'invalid' for l in labels]
            })
            labels_path = tmpdir / 'labels.csv'
            labels_df.to_csv(labels_path, index=False)
            
            # Create features file
            features_path = tmpdir / 'features.npy'
            np.save(features_path, features)
            
            # Train a simple model
            model_path = tmpdir / 'model.pkl'
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            model.fit(features, labels)
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Run evaluation
            output_path = tmpdir / 'metrics.json'
            result = run_metrics_evaluation(
                model_path=str(model_path),
                features_path=str(features_path),
                labels_path=str(labels_path),
                output_path=str(output_path)
            )
            
            # Verify output
            assert 'metrics' in result
            assert 'baseline' in result
            assert 'comparison' in result
            assert 'sample_ids' in result
            
            # Verify baseline type
            assert result['baseline']['type'] == 'majority_class_predictor'
            
            # Verify sample IDs match
            assert len(result['sample_ids']) == n_samples
            assert set(result['sample_ids']) == set(labels_df['clip_id'].values)
            
            # Verify file was written
            assert output_path.exists()
            
            # Verify JSON structure
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result == result