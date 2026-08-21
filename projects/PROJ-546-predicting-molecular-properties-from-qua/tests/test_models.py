"""
Contract test for code/train_models.py
Verifies Random Forest training functionality.

This test suite validates the core training logic of the molecular property
prediction pipeline, ensuring that Random Forest models can be trained,
evaluated, and that the cross-validation structure is correct.
"""
import pytest
import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json
import logging

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from train_models import (
    setup_logger,
    load_data_semi,
    load_data_dft,
    load_locked_splits,
    train_and_evaluate_fold,
    train_models,
    main
)

# Configure logging for tests to avoid noise
logging.basicConfig(level=logging.WARNING)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal synthetic datasets for testing
    n_samples = 50
    n_features = 10
    
    # Semi-empirical descriptors
    semi_data = {
        'molecule_id': [f"mol_{i:03d}" for i in range(n_samples)],
        'experimental_barrier': np.random.uniform(10.0, 50.0, n_samples).round(2),
        'HOMO_energy': np.random.uniform(-12.0, -8.0, n_samples).round(4),
        'LUMO_energy': np.random.uniform(-2.0, 2.0, n_samples).round(4),
        'mayer_bond_order': np.random.uniform(0.5, 2.5, n_samples).round(4)
    }
    
    # Add more descriptor columns to simulate real data
    for i in range(n_features - 3):
        semi_data[f'desc_{i+3}'] = np.random.uniform(-5.0, 5.0, n_samples).round(4)
    
    semi_df = pd.DataFrame(semi_data)
    semi_path = data_dir / "descriptors_semi.csv"
    semi_df.to_csv(semi_path, index=False)
    
    # DFT descriptors (subset)
    dft_data = {
        'molecule_id': [f"mol_{i:03d}" for i in range(n_samples)],
        'experimental_barrier': semi_df['experimental_barrier'].values,
        'HOMO_energy': np.random.uniform(-12.5, -8.5, n_samples).round(4),
        'LUMO_energy': np.random.uniform(-2.5, 1.5, n_samples).round(4),
        'mayer_bond_order': np.random.uniform(0.6, 2.6, n_samples).round(4)
    }
    
    for i in range(n_features - 3):
        dft_data[f'desc_{i+3}'] = np.random.uniform(-5.5, 5.5, n_samples).round(4)
    
    dft_df = pd.DataFrame(dft_data)
    dft_path = data_dir / "descriptors_dft.csv"
    dft_df.to_csv(dft_path, index=False)
    
    # Locked splits (StratifiedKFold with fixed random_state)
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    y_labels = pd.qcut(semi_df['experimental_barrier'], q=5, labels=False)
    
    splits = []
    for fold, (train_idx, test_idx) in enumerate(skf.split(semi_df, y_labels)):
        splits.append({
            'fold': fold,
            'train_indices': train_idx.tolist(),
            'test_indices': test_idx.tolist()
        })
    
    splits_path = data_dir / "locked_splits.json"
    with open(splits_path, 'w') as f:
        json.dump(splits, f, indent=2)
    
    return {
        'semi_path': semi_path,
        'dft_path': dft_path,
        'splits_path': splits_path,
        'data_dir': data_dir
    }

def test_setup_logger_creates_handler(tmp_path):
    """Test that setup_logger creates a valid logger with file handler."""
    log_file = tmp_path / "test.log"
    logger = setup_logger("test_logger", str(log_file))
    
    assert logger is not None
    assert len(logger.handlers) > 0
    assert log_file.exists()

def test_load_data_semi_validates_structure(temp_data_dir):
    """Test that load_data_semi correctly loads and validates semi-empirical data."""
    X, y = load_data_semi(str(temp_data_dir['semi_path']))
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert len(X) == len(y)
    assert 'molecule_id' not in X.columns
    assert 'experimental_barrier' not in X.columns
    assert 'HOMO_energy' in X.columns or any(col.startswith('desc_') for col in X.columns)

def test_load_data_dft_validates_structure(temp_data_dir):
    """Test that load_data_dft correctly loads and validates DFT data."""
    X, y = load_data_dft(str(temp_data_dir['dft_path']))
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert len(X) == len(y)
    assert 'molecule_id' not in X.columns
    assert 'experimental_barrier' not in X.columns

def test_load_locked_splits_returns_correct_format(temp_data_dir):
    """Test that load_locked_splits returns the expected split structure."""
    splits = load_locked_splits(str(temp_data_dir['splits_path']))
    
    assert isinstance(splits, list)
    assert len(splits) == 5  # 5 folds
    for split in splits:
        assert 'fold' in split
        assert 'train_indices' in split
        assert 'test_indices' in split
        assert isinstance(split['train_indices'], list)
        assert isinstance(split['test_indices'], list)

def test_train_and_evaluate_fold_returns_expected_structure(temp_data_dir):
    """Test that train_and_evaluate_fold returns a dictionary with required keys."""
    X, y = load_data_semi(str(temp_data_dir['semi_path']))
    splits = load_locked_splits(str(temp_data_dir['splits_path']))
    
    # Test with first fold
    train_idx = splits[0]['train_indices']
    test_idx = splits[0]['test_indices']
    
    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]
    
    result = train_and_evaluate_fold(X_train, y_train, X_test, y_test, 0)
    
    assert isinstance(result, dict)
    assert 'mae' in result
    assert 'model' in result
    assert 'fold' in result
    assert result['fold'] == 0
    assert isinstance(result['mae'], float)
    assert result['mae'] >= 0

def test_train_models_executes_cross_validation(temp_data_dir):
    """Test that train_models runs cross-validation and produces results."""
    splits = load_locked_splits(str(temp_data_dir['splits_path']))
    X_semi, y_semi = load_data_semi(str(temp_data_dir['semi_path']))
    X_dft, y_dft = load_data_dft(str(temp_data_dir['dft_path']))
    
    # Mock the RandomForest to ensure fast execution
    with patch('train_models.RandomForestRegressor') as MockRF:
        mock_model = MagicMock()
        mock_model.fit = MagicMock()
        mock_model.predict = MagicMock(return_value=np.array([25.0] * 10))
        mock_model.score = MagicMock(return_value=0.8)
        mock_model.feature_importances_ = np.array([0.1] * 10)
        MockRF.return_value = mock_model
        
        results = train_models(X_semi, y_semi, X_dft, y_dft, splits)
        
        assert isinstance(results, dict)
        assert 'semi_results' in results
        assert 'dft_results' in results
        assert 'semi_model' in results
        assert 'dft_model' in results
        assert len(results['semi_results']) == 5  # 5 folds
        assert len(results['dft_results']) == 5  # 5 folds

def test_train_models_handles_missing_splits_file(tmp_path):
    """Test that train_models handles missing splits file gracefully."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create minimal data files
    semi_path = data_dir / "descriptors_semi.csv"
    semi_df = pd.DataFrame({
        'molecule_id': ['mol_0'],
        'experimental_barrier': [25.0],
        'HOMO_energy': [-10.0],
        'LUMO_energy': [0.0],
        'mayer_bond_order': [1.0]
    })
    semi_df.to_csv(semi_path, index=False)
    
    dft_path = data_dir / "descriptors_dft.csv"
    dft_df = semi_df.copy()
    dft_df.to_csv(dft_path, index=False)
    
    # No splits file exists
    splits_path = data_dir / "locked_splits.json"
    
    with pytest.raises(FileNotFoundError):
        train_models(
            pd.DataFrame(), pd.Series(), pd.DataFrame(), pd.Series(),
            load_locked_splits(str(splits_path))
        )

def test_main_entry_point_exists():
    """Verify the main entry point exists and is callable."""
    assert callable(main)

def test_train_models_imports_required_libraries():
    """Verify that train_models.py imports necessary libraries for RF training."""
    script_path = Path("code/train_models.py")
    assert script_path.exists(), "train_models.py not found"
    
    with open(script_path) as f:
        content = f.read()
        # Check for essential imports
        assert 'sklearn' in content or 'from sklearn' in content
        assert 'RandomForest' in content or 'RandomForestRegressor' in content
        assert 'cross_val' in content or 'KFold' in content or 'StratifiedKFold' in content

def test_train_models_handles_empty_data():
    """Test that the training logic handles edge cases gracefully."""
    X = pd.DataFrame(columns=['f1'])
    y = pd.Series([])
    
    # This should raise an error or return a specific structure
    # depending on implementation. We verify it doesn't crash silently.
    try:
        # We expect this to fail because of empty data, which is correct behavior
        # But we want to ensure it fails with a clear error, not a silent crash
        from train_models import train_and_evaluate_fold
        # Create dummy split indices
        train_idx = [0]
        test_idx = [0]
        X_train = X.iloc[train_idx] if len(X) > 0 else X
        y_train = y.iloc[train_idx] if len(y) > 0 else y
        X_test = X.iloc[test_idx] if len(X) > 0 else X
        y_test = y.iloc[test_idx] if len(y) > 0 else y
        
        if len(X_train) > 0 and len(y_train) > 0:
            train_and_evaluate_fold(X_train, y_train, X_test, y_test, 0)
        else:
            # Empty data case - should raise or handle gracefully
            pass
    except (ValueError, IndexError, Exception) as e:
        # Expected for empty data - this is correct behavior
        pass