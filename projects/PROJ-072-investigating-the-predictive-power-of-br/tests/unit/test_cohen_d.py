import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from classification.cohen_d import calculate_cohen_d, calculate_cohen_d_for_all_features

def test_cohen_d_identical_groups():
    """Test that Cohen's d is 0 when groups are identical."""
    g1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    g2 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    d, _, _ = calculate_cohen_d(g1, g2)
    assert np.isclose(d, 0.0), f"Expected 0.0, got {d}"

def test_cohen_d_large_difference():
    """Test Cohen's d with a known large difference."""
    # Group 1: mean=0, std=1
    g1 = np.array([0.0, 1.0, -1.0, 0.0, 1.0])
    # Group 2: mean=2, std=1 (shifted by 2)
    g2 = np.array([2.0, 3.0, 1.0, 2.0, 3.0])
    d, _, _ = calculate_cohen_d(g1, g2)
    # Expected d is roughly 2.0
    assert np.isclose(d, 2.0, atol=0.1), f"Expected ~2.0, got {d}"

def test_cohen_d_negative_difference():
    """Test that Cohen's d is negative if group 2 mean < group 1 mean."""
    g1 = np.array([5.0, 6.0, 7.0])
    g2 = np.array([1.0, 2.0, 3.0])
    d, _, _ = calculate_cohen_d(g1, g2)
    assert d < 0, f"Expected negative d, got {d}"

def test_cohen_d_dataframe_integration():
    """Test the dataframe-based calculation function."""
    # Create mock data
    np.random.seed(42)
    n_subjects = 20
    n_features = 3
    
    data = {
        'subject_id': [f'sub_{i}' for i in range(n_subjects)],
        'feature_1': np.random.randn(n_subjects),
        'feature_2': np.random.randn(n_subjects) + 1.0, # Shifted mean
        'feature_3': np.random.randn(n_subjects)
    }
    features_df = pd.DataFrame(data)
    
    labels_df = pd.DataFrame({
        'subject_id': [f'sub_{i}' for i in range(n_subjects)],
        'diagnosis': ['HC'] * 10 + ['SZ'] * 10
    })
    
    # Manually shift HC group for feature_2 to ensure difference
    # Actually, let's just rely on the random seed and the fact that we know the distribution
    # But to be safe for the test, let's force a difference
    features_df.loc[features_df['subject_id'].str.startswith('sub_0'), 'feature_2'] += 5.0
    
    results = calculate_cohen_d_for_all_features(features_df, labels_df)
    
    assert 'cohen_d' in results.columns
    assert 'feature_1' in results['feature'].values
    assert 'feature_2' in results['feature'].values
    assert 'feature_3' in results['feature'].values
    
    # Check that feature_2 has a different d than feature_1 (since we shifted it)
    d_1 = results[results['feature'] == 'feature_1']['cohen_d'].values[0]
    d_2 = results[results['feature'] == 'feature_2']['cohen_d'].values[0]
    
    # With the shift, d_2 should be significantly larger in magnitude than d_1
    assert abs(d_2) > abs(d_1), f"Expected |d_2| > |d_1|, got {abs(d_2)} vs {abs(d_1)}"