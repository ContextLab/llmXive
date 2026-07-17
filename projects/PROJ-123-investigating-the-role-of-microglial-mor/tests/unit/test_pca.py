import pytest
import pandas as pd
import numpy as np
import json
import os
from code.analysis import run_pca_if_needed, run_vif_analysis
from code.config import get_path

@pytest.fixture
def sample_data():
    """Create a sample dataframe with high correlation features to trigger PCA."""
    np.random.seed(42)
    n = 100
    # Create correlated features
    base = np.random.randn(n)
    data = {
        'subject_id': range(n),
        'feature_a': base,
        'feature_b': base * 2 + np.random.randn(n) * 0.1, # Highly correlated
        'feature_c': base * 0.5 + np.random.randn(n) * 0.1, # Highly correlated
        'cognitive_score': np.random.randn(n),
        'brain_region': ['A'] * 50 + ['B'] * 50,
        'pathology_status': ['Control'] * 50 + ['AD'] * 50,
        'amyloid_beta': np.random.randn(n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def vif_triggered_path(sample_data, tmp_path):
    """Simulate a VIF check result that triggers PCA."""
    # Manually create a vif_check.json that triggers PCA
    # We mock the VIF scores to be high
    vif_data = {
        "vif_scores": [
            {"feature": "feature_a", "VIF": 10.0},
            {"feature": "feature_b", "VIF": 10.0},
            {"feature": "feature_c", "VIF": 10.0}
        ],
        "max_vif": 10.0,
        "trigger_pca": True,
        "threshold": 5.0
    }
    output_dir = os.path.join(tmp_path, "data", "intermediates")
    os.makedirs(output_dir, exist_ok=True)
    vif_path = os.path.join(output_dir, "vif_check.json")
    with open(vif_path, 'w') as f:
        json.dump(vif_data, f)
    return vif_path

@pytest.fixture
def vif_not_triggered_path(sample_data, tmp_path):
    """Simulate a VIF check result that does NOT trigger PCA."""
    vif_data = {
        "vif_scores": [
            {"feature": "feature_a", "VIF": 1.0},
            {"feature": "feature_b", "VIF": 1.0},
            {"feature": "feature_c", "VIF": 1.0}
        ],
        "max_vif": 1.0,
        "trigger_pca": False,
        "threshold": 5.0
    }
    output_dir = os.path.join(tmp_path, "data", "intermediates")
    os.makedirs(output_dir, exist_ok=True)
    vif_path = os.path.join(output_dir, "vif_check.json")
    with open(vif_path, 'w') as f:
        json.dump(vif_data, f)
    return vif_path

def test_pca_applied_when_triggered(sample_data, vif_triggered_path, tmp_path):
    """Test that PCA is applied when vif_check.json indicates trigger_pca=True."""
    # Mock the get_path function to return our temp path for the vif file
    # Since get_path is imported, we need to patch it or ensure the file exists in the expected relative location.
    # For this test, we will temporarily move the file to the expected location or patch get_path.
    # Easier approach: Create the file in the actual project's expected location if we can, 
    # but in a test environment, we should mock.
    # However, the function run_pca_if_needed uses get_path("data/intermediates/vif_check.json").
    # We will copy the temp file to the project root's data/intermediates for the test duration.
    
    project_root = get_path("") # Get project root
    target_dir = os.path.join(project_root, "data", "intermediates")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "vif_check.json")
    
    # Backup if exists
    backup = None
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            backup = f.read()
    
    # Write test file
    with open(target_path, 'w') as f:
        json.dump(json.load(open(vif_triggered_path)), f)
    
    try:
        feature_cols = ['feature_a', 'feature_b', 'feature_c']
        df_out, pca_applied = run_pca_if_needed(sample_data, feature_cols)
        
        assert pca_applied is True, "PCA should be applied when trigger_pca is True."
        # Check that original feature columns are dropped
        assert 'feature_a' not in df_out.columns
        assert 'feature_b' not in df_out.columns
        assert 'feature_c' not in df_out.columns
        # Check that PC columns exist
        assert 'PC1' in df_out.columns
        assert 'PC2' in df_out.columns
        assert 'PC3' in df_out.columns
        # Check orthogonality (covariance should be near zero)
        pca_features = df_out[['PC1', 'PC2', 'PC3']]
        cov_matrix = pca_features.cov()
        # Diagonal should be non-zero, off-diagonal near zero
        assert abs(cov_matrix.loc['PC1', 'PC2']) < 0.01
        assert abs(cov_matrix.loc['PC1', 'PC3']) < 0.01
        assert abs(cov_matrix.loc['PC2', 'PC3']) < 0.01
    finally:
        # Restore backup
        if backup:
            with open(target_path, 'w') as f:
                f.write(backup)
        else:
            if os.path.exists(target_path):
                os.remove(target_path)

def test_pca_skipped_when_not_triggered(sample_data, vif_not_triggered_path, tmp_path):
    """Test that PCA is skipped when vif_check.json indicates trigger_pca=False."""
    project_root = get_path("")
    target_dir = os.path.join(project_root, "data", "intermediates")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "vif_check.json")
    
    backup = None
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            backup = f.read()
    
    with open(target_path, 'w') as f:
        json.dump(json.load(open(vif_not_triggered_path)), f)
    
    try:
        feature_cols = ['feature_a', 'feature_b', 'feature_c']
        df_out, pca_applied = run_pca_if_needed(sample_data, feature_cols)
        
        assert pca_applied is False, "PCA should NOT be applied when trigger_pca is False."
        # Check that original feature columns are preserved
        assert 'feature_a' in df_out.columns
        assert 'feature_b' in df_out.columns
        assert 'feature_c' in df_out.columns
        # Check that PC columns do NOT exist
        assert 'PC1' not in df_out.columns
    finally:
        if backup:
            with open(target_path, 'w') as f:
                f.write(backup)
        else:
            if os.path.exists(target_path):
                os.remove(target_path)

def test_pca_fails_if_vif_file_missing(sample_data, tmp_path):
    """Test that run_pca_if_needed raises FileNotFoundError if vif_check.json is missing."""
    project_root = get_path("")
    target_dir = os.path.join(project_root, "data", "intermediates")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, "vif_check.json")
    
    # Ensure file does not exist
    if os.path.exists(target_path):
        os.remove(target_path)
    
    feature_cols = ['feature_a', 'feature_b', 'feature_c']
    with pytest.raises(FileNotFoundError, match="VIF check file.*not found"):
        run_pca_if_needed(sample_data, feature_cols)
