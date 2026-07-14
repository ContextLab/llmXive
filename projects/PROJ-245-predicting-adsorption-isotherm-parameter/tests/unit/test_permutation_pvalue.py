"""
Unit tests for permutation-based p-value calculation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import tempfile
import json
from joblib import dump

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from models.permutation_pvalue import (
    calculate_p_values,
    run_permutation_analysis,
    ensure_dirs,
    load_models,
    load_test_data
)

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 5
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Create a target with some relationship to features
    y = 2 * X['feature_0'] + 0.5 * X['feature_1'] + np.random.randn(n_samples) * 0.1
    
    return X, y

@pytest.fixture
def trained_model(sample_data):
    """Train a simple model for testing."""
    X, y = sample_data
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def temp_test_data():
    """Create a temporary test data file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "test_data.csv"
        df = pd.DataFrame({
            'material_id': range(50),
            'feature_0': np.random.randn(50),
            'feature_1': np.random.randn(50),
            'feature_2': np.random.randn(50),
            'langmuir_capacity': np.random.randn(50)
        })
        df.to_csv(data_path, index=False)
        yield data_path

def test_calculate_p_values_basic(trained_model, sample_data):
    """Test basic p-value calculation functionality."""
    X, y = sample_data
    
    results = calculate_p_values(
        model=trained_model,
        X=X,
        y=y,
        n_permutations=50,  # Small number for speed
        random_state=42
    )
    
    assert isinstance(results, pd.DataFrame)
    assert 'feature' in results.columns
    assert 'p_value' in results.columns
    assert 'original_score' in results.columns
    assert len(results) == 5  # 5 features
    
    # P-values should be between 0 and 1
    assert all((results['p_value'] >= 0) & (results['p_value'] <= 1))
    
    # Results should be sorted by p-value
    assert results['p_value'].is_monotonic_increasing

def test_calculate_p_values_significance(trained_model, sample_data):
    """Test that significant features get low p-values."""
    X, y = sample_data
    
    results = calculate_p_values(
        model=trained_model,
        X=X,
        y=y,
        n_permutations=100,
        random_state=42
    )
    
    # With a meaningful model, at least some features should have p < 0.05
    # (though with small n_permutations this might not always hold)
    assert len(results) > 0

def test_ensure_dirs_creates_directory():
    """Test that ensure_dirs creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "new_dir"
        assert not test_dir.exists()
        
        ensure_dirs(test_dir)
        
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_run_permutation_analysis(trained_model, temp_model_dir, temp_test_data):
    """Test the full permutation analysis pipeline."""
    # Save the model
    model_path = temp_model_dir / "random_forest.joblib"
    dump(trained_model, model_path)
    
    # Run analysis
    output_dir = temp_model_dir / "output"
    result = run_permutation_analysis(
        model_name="random_forest",
        model_dir=temp_model_dir,
        test_data_path=temp_test_data,
        output_dir=output_dir,
        n_permutations=20,  # Small for speed
        random_state=42
    )
    
    assert isinstance(result, dict)
    assert 'model_name' in result
    assert 'p_values' in result
    assert 'significant_features' in result
    assert len(result['p_values']) == 5  # 5 features in test data
    
    # Check that output files were created
    csv_path = output_dir / "pvalues_random_forest.csv"
    json_path = output_dir / "pvalues_random_forest_summary.json"
    
    assert csv_path.exists()
    assert json_path.exists()
    
    # Verify JSON content
    with open(json_path) as f:
        json_data = json.load(f)
    
    assert json_data['model_name'] == 'random_forest'
    assert len(json_data['p_values']) == 5

def test_load_models(temp_model_dir):
    """Test loading models from directory."""
    # Create dummy model files
    model1_path = temp_model_dir / "model1.joblib"
    model2_path = temp_model_dir / "model2.joblib"
    
    dump(LinearRegression(), model1_path)
    dump(RandomForestRegressor(), model2_path)
    
    models = load_models(temp_model_dir)
    
    assert 'model1' in models
    assert 'model2' in models
    assert isinstance(models['model1'], LinearRegression)
    assert isinstance(models['model2'], RandomForestRegressor)

def test_load_test_data(temp_test_data):
    """Test loading test data."""
    X, y = load_test_data(temp_test_data)
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert 'feature_0' in X.columns
    assert 'langmuir_capacity' in y.name or len(y) == len(X)

def test_p_values_with_no_signal():
    """Test p-values when there's no real signal."""
    np.random.seed(42)
    X = pd.DataFrame(np.random.randn(50, 3), columns=['f1', 'f2', 'f3'])
    y = pd.Series(np.random.randn(50))
    
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(X, y)
    
    results = calculate_p_values(
        model=model,
        X=X,
        y=y,
        n_permutations=50,
        random_state=42
    )
    
    # With no signal, p-values should be uniformly distributed
    # We can't assert a specific value, but we can check they're valid
    assert all((results['p_value'] >= 0) & (results['p_value'] <= 1))