import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from t032_permutation_null_fpr import (
    generate_null_dataset,
    estimate_fpr_for_dataset,
    write_output
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with known structure."""
    np.random.seed(42)
    n = 100
    data = {
        'predictor1': np.random.normal(0, 1, n),
        'predictor2': np.random.normal(0, 1, n),
        'target': np.random.normal(0, 1, n)  # No true relationship
    }
    df = pd.DataFrame(data)
    df.name = "test_dataset"
    return df

def test_generate_null_dataset_preserves_structure(sample_dataframe):
    """Test that null dataset generation preserves dataframe structure."""
    null_df = generate_null_dataset(sample_dataframe, 'target', seed=123)
    
    # Check structure is preserved
    assert list(null_df.columns) == list(sample_dataframe.columns)
    assert len(null_df) == len(sample_dataframe)
    
    # Check that predictor values are unchanged
    assert np.array_equal(null_df['predictor1'].values, sample_dataframe['predictor1'].values)
    assert np.array_equal(null_df['predictor2'].values, sample_dataframe['predictor2'].values)
    
    # Check that target values are shuffled (should be different order)
    assert not np.array_equal(null_df['target'].values, sample_dataframe['target'].values)
    # But the set of values should be the same
    assert set(null_df['target'].values) == set(sample_dataframe['target'].values)

def test_generate_null_dataset_deterministic(sample_dataframe):
    """Test that null dataset generation is deterministic with same seed."""
    null_df1 = generate_null_dataset(sample_dataframe, 'target', seed=42)
    null_df2 = generate_null_dataset(sample_dataframe, 'target', seed=42)
    
    assert np.array_equal(null_df1['target'].values, null_df2['target'].values)

def test_estimate_fpr_returns_valid_structure(sample_dataframe):
    """Test that FPR estimation returns a valid result structure."""
    result = estimate_fpr_for_dataset(
        sample_dataframe,
        'target',
        ['predictor1', 'predictor2'],
        n_permutations=10,  # Small number for test speed
        seed=42
    )
    
    assert 'dataset_name' in result
    assert 'n_permutations' in result
    assert 'total_tests' in result
    assert 'significant_tests' in result
    assert 'fpr' in result
    assert 'alpha' in result
    
    assert result['n_permutations'] == 10
    assert 0 <= result['fpr'] <= 1
    assert result['alpha'] == 0.05

def test_write_output_creates_json():
    """Test that write_output creates a valid JSON file."""
    results = [
        {
            'dataset_name': 'test',
            'n_permutations': 10,
            'total_tests': 20,
            'significant_tests': 1,
            'fpr': 0.05,
            'alpha': 0.05,
            'p_values_sample': [0.1, 0.2, 0.3]
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_null_fpr.json')
        write_output(results, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert 'generated_at' in data
        assert 'results' in data
        assert len(data['results']) == 1
        assert data['results'][0]['fpr'] == 0.05

def test_fpr_around_alpha_for_null_data(sample_dataframe):
    """
    Test that FPR is approximately alpha when there is no true relationship.
    This is a statistical sanity check.
    """
    result = estimate_fpr_for_dataset(
        sample_dataframe,
        'target',
        ['predictor1', 'predictor2'],
        n_permutations=50,  # Small for test speed, but enough for sanity check
        alpha=0.05,
        seed=42
    )
    
    # FPR should be close to alpha (0.05) with some variance due to sampling
    # With only 50 permutations, we expect a wide range, but it should be reasonable
    assert 0 <= result['fpr'] <= 0.20  # Allow some variance for small sample
    assert result['total_tests'] > 0
