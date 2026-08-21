import os
import sys
import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Ensure code/ is in path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from classification.models import run_classification_pipeline
from classification.validation import run_validation_pipeline

@pytest.mark.integration
def test_full_pipeline():
    """
    Integration test for full classification pipeline.
    
    Runs the classification pipeline on a small subset of data with shuffled labels.
    Verifies that:
    1. data/processed/results.json is created
    2. It contains required keys: 'accuracy', 'p_value', 'mde', 'significance_flag'
    3. significance_flag is False when labels are shuffled (no predictive power)
    """
    # Setup paths
    data_dir = project_root / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_path = data_dir / "results.json"
    
    # Clean up previous results if they exist
    if results_path.exists():
        results_path.unlink()
    
    # Create a small synthetic dataset for integration testing
    # This is a controlled test scenario, not the main research data
    np.random.seed(42)
    n_subjects = 20
    n_features = 10
    
    # Generate random feature matrix
    features = np.random.randn(n_subjects, n_features)
    
    # Create shuffled labels (random binary)
    # This ensures there is NO real signal between features and labels
    labels = np.random.randint(0, 2, n_subjects)
    
    # Save features to CSV (simulating the output of T022)
    features_df = pd.DataFrame(features, columns=[f'feature_{i}' for i in range(n_features)])
    features_df['label'] = labels
    features_csv = data_dir / "features_test_subset.csv"
    features_df.to_csv(features_csv, index=False)
    
    # Create subject status file (required by models)
    status_data = []
    for i in range(n_subjects):
        status_data.append({
            'subject_id': f'sub-{i:03d}',
            'status': 'included',
            'reason': 'N/A'
        })
    status_df = pd.DataFrame(status_data)
    status_csv = data_dir / "subject_status_test.csv"
    status_df.to_csv(status_csv, index=False)
    
    try:
        # Run the classification pipeline with shuffled labels
        # The pipeline should handle the test data path
        run_classification_pipeline(
            features_path=str(features_csv),
            status_path=str(status_csv),
            label_column='label',
            output_path=str(results_path),
            n_permutations=100,  # Small number for testing
            random_state=42
        )
        
        # Verify results file exists
        assert results_path.exists(), "results.json was not created"
        
        # Load and verify contents
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Check required keys
        required_keys = ['accuracy', 'p_value', 'mde', 'significance_flag']
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"
        
        # Verify significance_flag is False when labels are shuffled
        # With shuffled labels, there should be no predictive power
        assert results['significance_flag'] is False, \
            f"significance_flag should be False for shuffled labels, but got {results['significance_flag']}"
        
        # Additional sanity checks
        assert 0.0 <= results['accuracy'] <= 1.0, "Accuracy should be between 0 and 1"
        assert 0.0 <= results['p_value'] <= 1.0, "p-value should be between 0 and 1"
        assert results['p_value'] > 0.05, \
            f"p-value should be > 0.05 for shuffled labels, but got {results['p_value']}"
        
    finally:
        # Cleanup test files
        if features_csv.exists():
            features_csv.unlink()
        if status_csv.exists():
            status_csv.unlink()
        # Keep results.json for inspection if needed, or remove it
        # results_path.unlink()
