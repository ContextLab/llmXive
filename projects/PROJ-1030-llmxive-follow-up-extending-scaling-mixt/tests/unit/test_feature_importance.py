import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

# Import the module functions
import sys
sys.path.insert(0, 'code')

from classification.feature_importance import (
    load_filtered_data_for_importance,
    compute_shap_values,
    compute_permutation_importance,
    analyze_importance_against_baseline,
    generate_interpretation_report
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    n_samples = 100
    n_features = 10
    
    # Create synthetic features
    features = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Create synthetic labels (binary)
    labels = pd.DataFrame({
        'label': np.random.randint(0, 2, n_samples)
    })
    
    return features, labels

@pytest.fixture
def trained_model(sample_data):
    """Create a simple trained model for testing."""
    features, labels = sample_data
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(features, labels['label'])
    return model

@pytest.fixture
def temp_files(tmp_path):
    """Create temporary files for testing."""
    features_path = tmp_path / "filtered_train.csv"
    labels_path = tmp_path / "labels.csv"
    model_path = tmp_path / "classifier.pkl"
    baseline_path = tmp_path / "baseline_f1.json"
    shap_output = tmp_path / "feature_importance.json"
    report_output = tmp_path / "shap_interpretation.md"
    
    # Save sample data
    features, labels = sample_data
    combined = pd.concat([features, labels], axis=1)
    combined.to_csv(features_path, index=False)
    
    # Save a dummy model
    import pickle
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    model.fit(features, labels['label'])
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save baseline
    baseline_data = {
        'majority_f1': 0.5,
        'model_f1': 0.75
    }
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)
    
    return {
        'features': features_path,
        'labels': labels_path,
        'model': model_path,
        'baseline': baseline_path,
        'shap_output': shap_output,
        'report_output': report_output
    }

def test_load_filtered_data_for_importance(sample_data, tmp_path):
    """Test loading filtered data for importance analysis."""
    features, labels = sample_data
    
    # Save to temp file
    combined = pd.concat([features, labels], axis=1)
    path = tmp_path / "test.csv"
    combined.to_csv(path, index=False)
    
    # Load back
    loaded_features, loaded_labels = load_filtered_data_for_importance(str(path), None)
    
    assert len(loaded_features) == len(features)
    assert len(loaded_labels) == len(labels)
    assert list(loaded_features.columns) == list(features.columns)

def test_compute_shap_values(trained_model, sample_data):
    """Test SHAP value computation."""
    features, _ = sample_data
    
    shap_results = compute_shap_values(trained_model, features, sample_size=50)
    
    assert 'shap_values' in shap_results
    assert 'feature_names' in shap_results
    assert 'mean_abs_shap' in shap_results
    assert 'importance_ranking' in shap_results
    assert len(shap_results['feature_names']) == features.shape[1]

def test_compute_permutation_importance(trained_model, sample_data):
    """Test permutation importance computation."""
    features, labels = sample_data
    
    perm_results = compute_permutation_importance(
        trained_model, features, labels['label'].values, 
        n_repeats=2, sample_size=50
    )
    
    assert 'mean_importance' in perm_results
    assert 'std_importance' in perm_results
    assert 'feature_names' in perm_results
    assert 'importance_ranking' in perm_results
    assert len(perm_results['feature_names']) == features.shape[1]

def test_analyze_importance_against_baseline(trained_model, sample_data, temp_files):
    """Test analysis against baseline."""
    features, _ = sample_data
    shap_results = compute_shap_values(trained_model, features, sample_size=50)
    
    with open(temp_files['baseline'], 'r') as f:
        baseline_results = json.load(f)
    
    analysis = analyze_importance_against_baseline(
        shap_results, baseline_results, features.columns.tolist()
    )
    
    assert 'baseline_f1' in analysis
    assert 'model_f1' in analysis
    assert 'top_features' in analysis
    assert 'interpretation' in analysis
    assert len(analysis['top_features']) == 5

def test_generate_interpretation_report(trained_model, sample_data, temp_files):
    """Test report generation."""
    features, labels = sample_data
    
    shap_results = compute_shap_values(trained_model, features, sample_size=50)
    perm_results = compute_permutation_importance(
        trained_model, features, labels['label'].values,
        n_repeats=2, sample_size=50
    )
    
    with open(temp_files['baseline'], 'r') as f:
        baseline_results = json.load(f)
    
    analysis = analyze_importance_against_baseline(
        shap_results, baseline_results, features.columns.tolist()
    )
    
    generate_interpretation_report(
        shap_results, perm_results, analysis, str(temp_files['report_output'])
    )
    
    # Check file exists and contains expected content
    assert os.path.exists(temp_files['report_output'])
    
    with open(temp_files['report_output'], 'r') as f:
        content = f.read()
    
    assert "Feature Importance Analysis Report" in content
    assert "Associational Framing" in content
    assert "FR-007" in content
    assert "causation" in content.lower() or "causal" in content.lower()