import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
from sklearn.ensemble import GradientBoostingRegressor
from scipy.stats import spearmanr

# Import functions to test
from code.modeling import (
    load_processed_data,
    train_gradient_boosting,
    train_random_forest,
    compute_shap_values,
    compute_permutation_importance,
    rank_features,
    calculate_spearman_correlation,
    distinguish_feature_categories,
    run_sensitivity_analysis_crosslinker_proxy
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    data = {
        'atomic_radius_variance': np.random.rand(100),
        'crosslinker_density': np.random.rand(100),
        'surface_roughness': np.random.rand(100),
        'adhesion_strength': np.random.rand(100) * 10
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
        return f.name

def test_load_processed_data(temp_csv_file):
    """Test loading processed data from CSV."""
    df = load_processed_data(temp_csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'adhesion_strength' in df.columns

def test_train_gradient_boosting(sample_data):
    """Test training Gradient Boosting model."""
    X = sample_data.drop(columns=['adhesion_strength']).values
    y = sample_data['adhesion_strength'].values
    
    model, metrics = train_gradient_boosting(X, y, cv_folds=3)
    
    assert isinstance(model, GradientBoostingRegressor)
    assert 'mean_r2' in metrics
    assert 'std_r2' in metrics
    assert isinstance(metrics['mean_r2'], float)

def test_train_random_forest(sample_data):
    """Test training Random Forest model."""
    X = sample_data.drop(columns=['adhesion_strength']).values
    y = sample_data['adhesion_strength'].values
    
    model, metrics = train_random_forest(X, y, cv_folds=3)
    
    assert isinstance(model, GradientBoostingRegressor.__bases__[0])  # RandomForestRegressor
    assert 'mean_r2' in metrics
    assert 'std_r2' in metrics

def test_rank_features(sample_data):
    """Test feature ranking."""
    X = sample_data.drop(columns=['adhesion_strength'])
    feature_names = X.columns.tolist()
    n_features = len(feature_names)
    
    # Create mock SHAP values
    shap_values = np.random.rand(n_features, 100)
    
    rankings = rank_features(shap_values, feature_names)
    
    assert isinstance(rankings, pd.DataFrame)
    assert 'feature' in rankings.columns
    assert 'mean_abs_shap' in rankings.columns
    assert len(rankings) == n_features

def test_calculate_spearman_correlation():
    """Test Spearman correlation calculation."""
    ranking1 = pd.Series([1, 2, 3, 4, 5])
    ranking2 = pd.Series([1, 2, 3, 4, 5])
    
    corr = calculate_spearman_correlation(ranking1, ranking2)
    
    assert corr == 1.0  # Perfect correlation

def test_distinguish_feature_categories():
    """Test feature category distinction."""
    features = [
        'atomic_radius_variance',
        'crosslinker_density',
        'surface_roughness',
        'rms_roughness',
        'skewness',
        'kurtosis'
    ]
    
    categories = distinguish_feature_categories(features)
    
    assert 'compositional' in categories
    assert 'surface' in categories
    assert 'atomic_radius_variance' in categories['compositional']
    assert 'crosslinker_density' in categories['compositional']
    assert 'surface_roughness' in categories['surface']
    assert 'rms_roughness' in categories['surface']

def test_run_sensitivity_analysis_crosslinker_proxy(temp_csv_file, temp_output_file):
    """Test sensitivity analysis report generation."""
    # Run the analysis
    result = run_sensitivity_analysis_crosslinker_proxy(temp_csv_file, temp_output_file)
    
    # Verify output file exists
    assert os.path.exists(temp_output_file)
    
    # Verify report content
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert 'definition' in result.columns
    assert 'model_r2' in result.columns
    assert 'model_rmse' in result.columns
    assert 'variance' in result.columns
    
    # Verify all expected definitions are present
    expected_definitions = ['ratio_A_B', 'inverse_ratio', 'log_ratio', 'squared_ratio']
    assert set(result['definition'].tolist()) == set(expected_definitions)

def test_run_sensitivity_analysis_missing_columns(temp_output_file):
    """Test sensitivity analysis with missing atomic columns."""
    # Create data without atomic fraction columns
    data = {
        'surface_roughness': np.random.rand(50),
        'adhesion_strength': np.random.rand(50) * 10
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df = pd.DataFrame(data)
        df.to_csv(f, index=False)
        input_file = f.name
    
    try:
        # Should handle missing columns gracefully
        result = run_sensitivity_analysis_crosslinker_proxy(input_file, temp_output_file)
        
        assert os.path.exists(temp_output_file)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
    finally:
        # Cleanup
        if os.path.exists(input_file):
            os.remove(input_file)
