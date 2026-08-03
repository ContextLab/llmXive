import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.diagnostics import (
    load_processed_data,
    calculate_vif,
    drop_high_vif_predictors,
    resolve_multicollinearity_and_retest
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with realistic predictor values."""
    np.random.seed(42)
    n_samples = 1000
    
    # Create synthetic but realistic data
    data = {
        'log_co_occurrence': np.random.normal(2.0, 1.0, n_samples),
        'flavor_similarity': np.random.uniform(0.0, 1.0, n_samples),
        'functional_role': np.random.choice(['primary', 'secondary', 'garnish'], n_samples),
        'compatibility_label': np.random.choice([0, 1], n_samples)
    }
    
    # Add some correlation to test VIF calculation
    # Make flavor_similarity slightly correlated with log_co_occurrence
    data['flavor_similarity'] = data['flavor_similarity'] + 0.3 * (data['log_co_occurrence'] - 2.0) / 3.0
    data['flavor_similarity'] = np.clip(data['flavor_similarity'], 0.0, 1.0)
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(tmp_path, sample_dataframe):
    """Create a temporary CSV file with sample data."""
    csv_path = tmp_path / "test_ingredient_pairs.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return str(csv_path)

def test_load_processed_data(temp_csv_path):
    """Test that load_processed_data correctly reads the CSV file."""
    df = load_processed_data(temp_csv_path)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'log_co_occurrence' in df.columns
    assert 'flavor_similarity' in df.columns
    assert 'functional_role' in df.columns
    assert 'compatibility_label' in df.columns

def test_load_processed_data_missing_file():
    """Test that load_processed_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_processed_data("nonexistent_file.csv")

def test_calculate_vif_basic(sample_dataframe):
    """Test basic VIF calculation on numeric predictors."""
    # Test with only numeric predictors
    numeric_cols = ['log_co_occurrence', 'flavor_similarity']
    vif_results = calculate_vif(sample_dataframe, numeric_cols)
    
    assert isinstance(vif_results, dict)
    assert len(vif_results) == 2
    assert 'log_co_occurrence' in vif_results
    assert 'flavor_similarity' in vif_results
    
    # VIF should be positive
    for col, vif in vif_results.items():
        assert vif > 0
        # VIF should not be infinite for uncorrelated data
        assert not np.isinf(vif)

def test_calculate_vif_with_categorical(sample_dataframe):
    """Test VIF calculation with categorical predictor."""
    predictor_cols = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
    vif_results = calculate_vif(sample_dataframe, predictor_cols)
    
    assert isinstance(vif_results, dict)
    # Should have entries for numeric cols and dummies for categorical
    assert len(vif_results) >= 3

def test_calculate_vif_zero_variance():
    """Test that VIF calculation raises error for zero variance column."""
    df = pd.DataFrame({
        'constant_col': [5.0] * 100,
        'normal_col': np.random.normal(0, 1, 100)
    })
    
    with pytest.raises(ValueError, match="zero variance"):
        calculate_vif(df, ['constant_col'])

def test_drop_high_vif_predictors():
    """Test identification of high VIF predictors."""
    vif_results = {
        'predictor_a': 2.5,
        'predictor_b': 6.0,
        'predictor_c': 1.2,
        'predictor_d': 8.5
    }
    
    high_vif = drop_high_vif_predictors(vif_results, threshold=5.0)
    
    assert 'predictor_b' in high_vif
    assert 'predictor_d' in high_vif
    assert 'predictor_a' not in high_vif
    assert 'predictor_c' not in high_vif
    assert len(high_vif) == 2

def test_drop_high_vif_predictors_threshold():
    """Test that threshold parameter works correctly."""
    vif_results = {
        'predictor_a': 4.9,
        'predictor_b': 5.0,
        'predictor_c': 5.1
    }
    
    # Threshold at 5.0 should include 5.1 but not 5.0
    high_vif = drop_high_vif_predictors(vif_results, threshold=5.0)
    assert 'predictor_c' in high_vif
    assert 'predictor_b' not in high_vif
    assert 'predictor_a' not in high_vif

def test_resolve_multicollinearity_and_retest(sample_dataframe):
    """Test iterative removal of high VIF predictors."""
    predictor_cols = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
    
    final_vif, removed = resolve_multicollinearity_and_retest(
        sample_dataframe, 
        predictor_cols, 
        vif_threshold=10.0  # High threshold to ensure no removal in this test
    )
    
    assert isinstance(final_vif, dict)
    assert isinstance(removed, list)
    # With high threshold, nothing should be removed
    assert len(removed) == 0

def test_vif_output_format(tmp_path, sample_dataframe):
    """Test that VIF results can be serialized to JSON."""
    predictor_cols = ['log_co_occurrence', 'flavor_similarity']
    vif_results = calculate_vif(sample_dataframe, predictor_cols)
    
    # This should not raise
    json_str = json.dumps(vif_results)
    assert isinstance(json_str, str)
    assert len(json_str) > 0