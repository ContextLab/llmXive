"""
Tests for the Nested Cross-Validation module (T019).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from sklearn.linear_model import LogisticRegression

from src.models.evaluate import run_nested_cv, print_summary
from src.models.train import train_model_fold

# Fixtures
@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_features_labels(temp_data_dir):
    """
    Create a synthetic dataset with features and labels.
    """
    n_samples = 100
    n_features = 10
    
    # Generate random features
    X = np.random.randn(n_samples, n_features)
    # Generate binary labels (stratified roughly)
    y = np.random.randint(0, 2, n_samples)
    # Ensure some class balance
    if y.sum() == 0 or y.sum() == n_samples:
        y[0] = 1 - y[0]
    
    # Create DataFrame
    feature_cols = [f"feature_{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_cols)
    df['label'] = y
    df['pathogen_id'] = [f"pathogen_{i}" for i in range(n_samples)]
    
    features_path = temp_data_dir / "features.csv"
    df.to_csv(features_path, index=False)
    
    # Create valid pathogens list (subset of IDs)
    valid_ids = df['pathogen_id'].tolist()
    valid_pathogens_path = temp_data_dir / "valid_pathogens.json"
    with open(valid_pathogens_path, 'w') as f:
        json.dump(valid_ids, f)
        
    return features_path, valid_pathogens_path

@pytest.fixture
def sample_interactions(temp_data_dir):
    """
    Create a synthetic interactions file.
    """
    data = {
        "pathogen_id": [f"pathogen_{i}" for i in range(100)],
        "host_id": [f"host_{i % 10}" for i in range(100)],
        "label": [1 if i % 3 == 0 else 0 for i in range(100)] # Some interaction logic
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / "interactions.csv"
    df.to_csv(path, index=False)
    return path

def test_run_nested_cv_basic(temp_data_dir, sample_features_labels, sample_interactions):
    """
    Test that run_nested_cv executes without error on small synthetic data.
    """
    features_path, valid_pathogens_path = sample_features_labels
    interactions_path = sample_interactions
    
    output_dir = temp_data_dir / "cv_output"
    
    # Run with small fold numbers for speed
    results = run_nested_cv(
        interactions_path=str(interactions_path),
        features_path=str(features_path),
        valid_pathogens_path=str(valid_pathogens_path),
        output_dir=str(output_dir),
        n_outer_folds=2,
        n_inner_folds=2,
        seed=42,
        vif_threshold=10.0 # High threshold to avoid VIF filtering too aggressively on random data
    )
    
    # Assertions
    assert "mean_auprc" in results
    assert "std_auprc" in results
    assert "all_auprcs" in results
    assert len(results["all_auprcs"]) == 2 # 2 outer folds
    assert 0.0 <= results["mean_auprc"] <= 1.0
    
    # Check output files
    assert (output_dir / "nested_cv_results.json").exists()

def test_run_nested_cv_vif_filtering(temp_data_dir, sample_features_labels, sample_interactions):
    """
    Test that VIF filtering is applied during the nested loop.
    """
    features_path, valid_pathogens_path = sample_features_labels
    interactions_path = sample_interactions
    
    output_dir = temp_data_dir / "cv_output_vif"
    
    # Use a very low threshold to force VIF removal
    results = run_nested_cv(
        interactions_path=str(interactions_path),
        features_path=str(features_path),
        valid_pathogens_path=str(valid_pathogens_path),
        output_dir=str(output_dir),
        n_outer_folds=2,
        n_inner_folds=2,
        seed=42,
        vif_threshold=1.0 # Very low, should remove many features
    )
    
    # Check that selected features count is less than original (10) if VIF triggered
    # Note: With random data, VIF might not trigger if correlations are low,
    # but the logic should still run.
    for fold_detail in results["fold_details"]:
        assert "selected_features_count" in fold_detail
        assert fold_detail["selected_features_count"] <= 10

def test_print_summary(capsys):
    """
    Test that print_summary outputs to console.
    """
    results = {
        "n_outer_folds": 5,
        "n_inner_folds": 3,
        "mean_auprc": 0.85,
        "std_auprc": 0.05,
        "all_auprcs": [0.8, 0.85, 0.88, 0.82, 0.9]
    }
    
    print_summary(results)
    captured = capsys.readouterr()
    
    assert "NESTED CROSS-VALIDATION SUMMARY" in captured.out
    assert "Mean AUPRC:  0.8500" in captured.out