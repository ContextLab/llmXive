import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

from src.models.feature_importance import (
    load_features_data,
    prepare_data,
    calculate_permutation_importance,
    rank_top_descriptors,
    run_feature_importance_analysis
)

@pytest.fixture
def sample_features_df():
    """Create a sample features DataFrame for testing."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'avg_electronegativity': np.random.uniform(1.5, 2.5, n_samples),
        'valence_electron_concentration': np.random.uniform(7, 9, n_samples),
        'atomic_radii_variance': np.random.uniform(0.01, 0.1, n_samples),
        'avg_d_electrons': np.random.uniform(5, 7, n_samples),
        'atomic_size_mismatch': np.random.uniform(0.02, 0.15, n_samples),
        'coercivity_Oe': np.random.uniform(10, 500, n_samples)
    }
    
    return pd.DataFrame(data)

@pytest.fixture
def temp_features_file(sample_features_df):
    """Create a temporary CSV file with sample features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_alloys_features.csv"
        sample_features_df.to_csv(filepath, index=False)
        yield filepath

def test_load_features_data(temp_features_file):
    """Test loading features data from CSV."""
    df = load_features_data(temp_features_file)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'avg_electronegativity' in df.columns
    assert 'coercivity_Oe' in df.columns

def test_load_features_data_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_features_data(Path("nonexistent_file.csv"))

def test_prepare_data(temp_features_file):
    """Test data preparation and splitting."""
    df = load_features_data(temp_features_file)
    X_train, X_test, y_train, y_test = prepare_data(df, test_size=0.2, random_state=42)
    
    assert len(X_train) == 80
    assert len(X_test) == 20
    assert len(y_train) == 80
    assert len(y_test) == 20
    assert list(X_train.columns) == [
        'avg_electronegativity',
        'valence_electron_concentration',
        'atomic_radii_variance',
        'avg_d_electrons',
        'atomic_size_mismatch'
    ]

def test_calculate_permutation_importance(temp_features_file):
    """Test permutation importance calculation."""
    from sklearn.ensemble import RandomForestRegressor
    
    df = load_features_data(temp_features_file)
    X_train, X_test, y_train, y_test = prepare_data(df, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=10, random_state=42, n_jobs=1)
    model.fit(X_train, y_train)
    
    importance_df = calculate_permutation_importance(
        model, X_train, y_train, X_test, y_test,
        n_repeats=5, random_state=42
    )
    
    assert isinstance(importance_df, pd.DataFrame)
    assert len(importance_df) == 5
    assert 'feature' in importance_df.columns
    assert 'importance_mean' in importance_df.columns
    assert 'importance_std' in importance_df.columns
    
    # Check sorting (descending by importance)
    assert importance_df['importance_mean'].iloc[0] >= importance_df['importance_mean'].iloc[-1]

def test_rank_top_descriptors():
    """Test ranking of top descriptors."""
    importance_df = pd.DataFrame({
        'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
        'importance_mean': [0.5, 0.3, 0.2, 0.1, 0.05],
        'importance_std': [0.1, 0.05, 0.02, 0.01, 0.005]
    })
    
    ranked = rank_top_descriptors(importance_df, top_n=3)
    
    assert len(ranked) == 3
    assert ranked[0]['rank'] == 1
    assert ranked[0]['feature'] == 'f1'
    assert ranked[0]['importance_mean'] == 0.5
    assert ranked[1]['rank'] == 2
    assert ranked[2]['rank'] == 3

def test_run_feature_importance_analysis(temp_features_file):
    """Test the full feature importance analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        results = run_feature_importance_analysis(
            features_path=temp_features_file,
            model_type='random_forest',
            output_dir=output_dir,
            n_repeats=5,
            test_size=0.2,
            random_state=42
        )
        
        assert isinstance(results, dict)
        assert results['model_type'] == 'random_forest'
        assert results['n_samples'] == 100
        assert results['n_features'] == 5
        assert results['top_feature'] is not None
        assert results['top_importance'] is not None
        
        # Check output files exist
        csv_path = Path(results['output_csv'])
        json_path = Path(results['output_json'])
        
        assert csv_path.exists()
        assert json_path.exists()
        
        # Verify CSV content
        output_df = pd.read_csv(csv_path)
        assert len(output_df) == 5
        assert 'feature' in output_df.columns
        
        # Verify JSON content
        import json
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert 'top_features' in json_data
        assert len(json_data['top_features']) == 5
        assert json_data['model_type'] == 'random_forest'

def test_run_feature_importance_analysis_linear(temp_features_file):
    """Test feature importance with linear regression model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        results = run_feature_importance_analysis(
            features_path=temp_features_file,
            model_type='linear',
            output_dir=output_dir,
            n_repeats=5,
            test_size=0.2,
            random_state=42
        )
        
        assert results['model_type'] == 'linear'
        assert Path(results['output_csv']).exists()
        assert Path(results['output_json']).exists()

def test_invalid_model_type(temp_features_file):
    """Test error handling for invalid model type."""
    with pytest.raises(ValueError, match="Unknown model_type"):
        run_feature_importance_analysis(
            features_path=temp_features_file,
            model_type='invalid_model',
            output_dir=Path("tmp"),
            n_repeats=5
        )

def test_missing_features_in_data():
    """Test error handling when features are missing."""
    df = pd.DataFrame({
        'avg_electronegativity': [1.0, 2.0],
        'coercivity_Oe': [100, 200]
        # Missing other required features
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "incomplete.csv"
        df.to_csv(filepath, index=False)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_features_data(filepath)