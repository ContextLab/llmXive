"""
Unit test for Random Forest training with 5-fold CV in tests/unit/test_trainer.py.

This test validates the core training logic in code/models/trainer.py.
It verifies that:
1. The trainer can load processed features and bin assignments.
2. The Random Forest model trains successfully with 5-fold CV.
3. Hyperparameter tuning via GridSearchCV functions correctly.
4. The model returns expected output structure (R2 score, best params).

Note: This test uses the 'Low' bin (0-2V) for validation as per US2 requirements.
"""

import os
import sys
import pytest
import tempfile
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from models.trainer import train_random_forest, run_training_pipeline
from data.binning import load_processed_features, assign_bins
from utils.constants import get_reactions_schema_template


@pytest.fixture
def sample_feature_data():
    """Generate a small synthetic feature matrix for testing."""
    # Create a deterministic small dataset mimicking real output
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'molecule_id': [f'MOL_{i:03d}' for i in range(n_samples)],
        'potential': [0 if i < 50 else 4 for i in range(n_samples)],  # 50 low, 50 high
        'homo': np.random.uniform(-6.0, -4.0, n_samples),
        'lumo': np.random.uniform(-1.0, 1.0, n_samples),
        'band_gap': np.random.uniform(2.0, 6.0, n_samples),
        'bond_length_avg': np.random.uniform(1.0, 2.0, n_samples),
        'bond_angle_avg': np.random.uniform(90.0, 120.0, n_samples),
        'dihedral_avg': np.random.uniform(-180.0, 180.0, n_samples),
        'decomp_energy': np.random.uniform(-0.5, 2.0, n_samples),  # Target variable
    }
    
    df = pd.DataFrame(data)
    return df


@pytest.fixture
def temp_processed_dir(sample_feature_data):
    """Create a temporary directory with processed feature CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        processed_dir = tmpdir_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Save sample features
        csv_path = processed_dir / "electrolyte_features.csv"
        sample_feature_data.to_csv(csv_path, index=False)
        
        # Save bin assignments (Low/High based on potential)
        bins_df = sample_feature_data.copy()
        bins_df['bin'] = bins_df['potential'].apply(lambda x: 'Low' if x < 3 else 'High')
        bins_path = processed_dir / "bins.csv"
        bins_df[['molecule_id', 'potential', 'bin']].to_csv(bins_path, index=False)
        
        yield tmpdir_path
        
        # Cleanup handled by TemporaryDirectory


def test_load_and_prepare_data(temp_processed_dir):
    """Test that data loading and preparation works correctly."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    # Load features
    df = load_processed_features(str(processed_dir / "electrolyte_features.csv"))
    
    assert len(df) > 0
    assert 'decomp_energy' in df.columns
    assert 'potential' in df.columns
    assert 'molecule_id' in df.columns


def test_train_random_forest_low_bin(temp_processed_dir):
    """Test Random Forest training on Low potential bin (0-2V)."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    # Train model on Low bin
    model, history = train_random_forest(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        target_column='decomp_energy',
        bin_filter='Low',
        n_estimators_search=[10, 20],  # Small search space for speed
        max_depth_search=[5, 10],
        cv_folds=3,  # Reduced for faster testing
        random_state=42
    )
    
    # Verify model exists
    assert model is not None
    assert hasattr(model, 'best_estimator_')
    
    # Verify history contains expected keys
    assert 'best_params' in history
    assert 'cv_results' in history
    assert 'r2_score' in history
    assert 'mae' in history
    
    # Verify R2 score is reasonable (not NaN or infinite)
    assert np.isfinite(history['r2_score'])
    assert not np.isnan(history['r2_score'])


def test_train_random_forest_high_bin(temp_processed_dir):
    """Test Random Forest training on High potential bin (4V)."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    # Train model on High bin
    model, history = train_random_forest(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        target_column='decomp_energy',
        bin_filter='High',
        n_estimators_search=[10, 20],
        max_depth_search=[5, 10],
        cv_folds=3,
        random_state=42
    )
    
    assert model is not None
    assert hasattr(model, 'best_estimator_')
    assert 'best_params' in history
    assert np.isfinite(history['r2_score'])


def test_hyperparameter_tuning_range(temp_processed_dir):
    """Test that GridSearchCV explores the specified hyperparameter space."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    model, history = train_random_forest(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        target_column='decomp_energy',
        bin_filter='Low',
        n_estimators_search=[5, 10, 15],
        max_depth_search=[3, 6, None],
        cv_folds=2,
        random_state=42
    )
    
    best_params = history['best_params']
    
    # Verify best_params contains expected keys
    assert 'n_estimators' in best_params
    assert 'max_depth' in best_params
    
    # Verify values are from the search space
    assert best_params['n_estimators'] in [5, 10, 15]
    assert best_params['max_depth'] in [3, 6, None]


def test_5fold_cv_structure(temp_processed_dir):
    """Test that 5-fold CV produces expected cross-validation structure."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    # Use a larger dataset for proper 5-fold
    df = load_processed_features(str(processed_dir / "electrolyte_features.csv"))
    if len(df[df['potential'] < 3]) < 20:
        # Duplicate rows to ensure enough samples for 5-fold
        low_mask = df['potential'] < 3
        low_df = df[low_mask]
        high_df = df[~low_mask]
        df = pd.concat([low_df, low_df, low_df, high_df], ignore_index=True)
        df.to_csv(str(processed_dir / "electrolyte_features.csv"), index=False)
    
    model, history = train_random_forest(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        target_column='decomp_energy',
        bin_filter='Low',
        n_estimators_search=[10],
        max_depth_search=[5],
        cv_folds=5,
        random_state=42
    )
    
    # Verify CV results structure
    cv_results = history['cv_results']
    assert 'mean_test_score' in cv_results
    assert 'std_test_score' in cv_results
    assert len(cv_results['mean_test_score']) > 0


def test_run_training_pipeline(temp_processed_dir):
    """Test the full training pipeline execution."""
    processed_dir = temp_processed_dir / "data" / "processed"
    output_dir = temp_processed_dir / "data" / "processed"
    
    # Run full pipeline
    results = run_training_pipeline(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        output_dir=str(output_dir),
        n_estimators_search=[10, 20],
        max_depth_search=[5, 10],
        cv_folds=3,
        random_state=42
    )
    
    # Verify results structure
    assert 'low_bin_model' in results
    assert 'high_bin_model' in results
    assert 'low_bin_history' in results
    assert 'high_bin_history' in results
    
    # Verify output files were created
    model_json_path = output_dir / "model_run.json"
    assert model_json_path.exists()
    
    # Verify JSON content
    with open(model_json_path, 'r') as f:
        model_data = json.load(f)
    
    assert 'low_bin_r2' in model_data
    assert 'high_bin_r2' in model_data
    assert 'low_bin_best_params' in model_data
    assert 'high_bin_best_params' in model_data


def test_model_serialization(temp_processed_dir):
    """Test that trained models can be serialized and deserialized."""
    processed_dir = temp_processed_dir / "data" / "processed"
    output_dir = temp_processed_dir / "data" / "processed"
    
    results = run_training_pipeline(
        features_path=str(processed_dir / "electrolyte_features.csv"),
        bins_path=str(processed_dir / "bins.csv"),
        output_dir=str(output_dir),
        n_estimators_search=[10],
        max_depth_search=[5],
        cv_folds=2,
        random_state=42
    )
    
    # Check that model artifacts exist
    low_model_path = output_dir / "low_bin_model.pkl"
    high_model_path = output_dir / "high_bin_model.pkl"
    
    assert low_model_path.exists()
    assert high_model_path.exists()


def test_error_handling_empty_bin(temp_processed_dir):
    """Test that the trainer handles empty bins gracefully."""
    processed_dir = temp_processed_dir / "data" / "processed"
    
    # Create a bin file with only 'Low' entries
    df = load_processed_features(str(processed_dir / "electrolyte_features.csv"))
    df_low_only = df[df['potential'] < 3].copy()
    
    bins_df = df_low_only.copy()
    bins_df['bin'] = 'Low'
    bins_df[['molecule_id', 'potential', 'bin']].to_csv(
        str(processed_dir / "bins.csv"), index=False
    )
    
    # This should raise an error or handle gracefully when 'High' bin is requested
    # but not 'Low'
    with pytest.raises(ValueError) as exc_info:
        train_random_forest(
            features_path=str(processed_dir / "electrolyte_features.csv"),
            bins_path=str(processed_dir / "bins.csv"),
            target_column='decomp_energy',
            bin_filter='High',  # No High data available
            n_estimators_search=[10],
            max_depth_search=[5],
            cv_folds=2,
            random_state=42
        )
    
    assert "No data found for bin" in str(exc_info.value)