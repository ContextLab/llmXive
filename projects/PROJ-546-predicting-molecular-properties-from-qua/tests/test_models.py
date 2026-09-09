"""
Contract tests for code/train_models.py (User Story 2).
Verifies Random Forest training logic, data loading, and split handling.
"""
import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from train_models import (
    load_data_semi,
    load_data_dft,
    load_locked_splits,
    train_and_evaluate_fold,
    train_models,
    setup_logger
)
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import mean_absolute_error


class MockLogger:
    """Minimal mock logger for testing without file I/O."""
    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass
    def debug(self, msg): pass


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data artifacts."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)


def test_load_data_semi_missing_file(temp_data_dir):
    """Test that load_data_semi raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_data_semi(os.path.join(temp_data_dir, "nonexistent.csv"))


def test_load_data_dft_missing_file(temp_data_dir):
    """Test that load_data_dft raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_data_dft(os.path.join(temp_data_dir, "nonexistent.csv"))


def test_load_locked_splits_missing_file(temp_data_dir):
    """Test that load_locked_splits raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_locked_splits(os.path.join(temp_data_dir, "nonexistent.json"))


def test_train_and_evaluate_fold_basic(temp_data_dir):
    """Test basic training and evaluation of a single fold."""
    # Create dummy data
    n_samples = 100
    n_features = 5
    X = np.random.rand(n_samples, n_features)
    y = np.random.rand(n_samples)
    
    # Create dummy split indices
    train_idx = np.arange(80)
    test_idx = np.arange(80, 100)
    
    # Train and evaluate
    mae, model = train_and_evaluate_fold(X, y, train_idx, test_idx)
    
    # Assertions
    assert isinstance(mae, float)
    assert mae >= 0
    assert isinstance(model, RandomForestRegressor)
    assert hasattr(model, 'predict')


def test_train_models_integration(temp_data_dir):
    """Test the full train_models workflow with dummy data."""
    # Create dummy descriptor files
    semi_path = os.path.join(temp_data_dir, "descriptors_semi.csv")
    dft_path = os.path.join(temp_data_dir, "descriptors_dft.csv")
    splits_path = os.path.join(temp_data_dir, "splits.json")
    
    # Generate dummy data
    n_samples = 200
    n_features = 10
    
    # Semi-empirical descriptors
    semi_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples) * 10,
        'LUMO_energy': np.random.rand(n_samples) * 10,
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(semi_data).to_csv(semi_path, index=False)
    
    # DFT descriptors
    dft_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples) * 10,
        'LUMO_energy': np.random.rand(n_samples) * 10,
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(dft_data).to_csv(dft_path, index=False)
    
    # Locked splits (using a simple binary target for stratification)
    # We'll create a dummy 'experimental_barrier' column for stratification
    experimental_barrier = np.random.choice([0, 1], n_samples)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    splits = []
    for train_idx, test_idx in skf.split(np.zeros(n_samples), experimental_barrier):
        splits.append({
            'train': train_idx.tolist(),
            'test': test_idx.tolist()
        })
    
    with open(splits_path, 'w') as f:
        json.dump(splits, f)
    
    # Mock logger
    logger = MockLogger()
    
    # Run training
    results = train_models(semi_path, dft_path, splits_path, logger=logger)
    
    # Assertions
    assert 'semi' in results
    assert 'dft' in results
    assert 'semi_maes' in results['semi']
    assert 'dft_maes' in results['dft']
    assert isinstance(results['semi_maes'], list)
    assert isinstance(results['dft_maes'], list)
    assert len(results['semi_maes']) == 5  # 5 folds
    assert len(results['dft_maes']) == 5
    assert all(isinstance(mae, float) for mae in results['semi_maes'])
    assert all(isinstance(mae, float) for mae in results['dft_maes'])


def test_train_models_handles_missing_data(temp_data_dir):
    """Test that train_models raises appropriate errors for missing files."""
    # Missing semi descriptors
    with pytest.raises(FileNotFoundError):
        train_models(
            os.path.join(temp_data_dir, "missing_semi.csv"),
            os.path.join(temp_data_dir, "descriptors_dft.csv"),
            os.path.join(temp_data_dir, "splits.json")
        )
    
    # Missing DFT descriptors
    with pytest.raises(FileNotFoundError):
        train_models(
            os.path.join(temp_data_dir, "descriptors_semi.csv"),
            os.path.join(temp_data_dir, "missing_dft.csv"),
            os.path.join(temp_data_dir, "splits.json")
        )
    
    # Missing splits
    with pytest.raises(FileNotFoundError):
        train_models(
            os.path.join(temp_data_dir, "descriptors_semi.csv"),
            os.path.join(temp_data_dir, "descriptors_dft.csv"),
            os.path.join(temp_data_dir, "missing_splits.json")
        )


def test_train_models_consistent_splits(temp_data_dir):
    """Test that both models use the same split indices."""
    # Create dummy data
    n_samples = 100
    semi_path = os.path.join(temp_data_dir, "descriptors_semi.csv")
    dft_path = os.path.join(temp_data_dir, "descriptors_dft.csv")
    splits_path = os.path.join(temp_data_dir, "splits.json")
    
    # Generate dummy data
    semi_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples),
        'LUMO_energy': np.random.rand(n_samples),
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(semi_data).to_csv(semi_path, index=False)
    
    dft_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples),
        'LUMO_energy': np.random.rand(n_samples),
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(dft_data).to_csv(dft_path, index=False)
    
    # Create locked splits
    experimental_barrier = np.random.choice([0, 1], n_samples)
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=123)
    splits = []
    for train_idx, test_idx in skf.split(np.zeros(n_samples), experimental_barrier):
        splits.append({
            'train': train_idx.tolist(),
            'test': test_idx.tolist()
        })
    
    with open(splits_path, 'w') as f:
        json.dump(splits, f)
    
    # Run training
    logger = MockLogger()
    results = train_models(semi_path, dft_path, splits_path, logger=logger)
    
    # Verify that both models were trained on the same splits
    # by checking that the number of folds matches
    assert len(results['semi_maes']) == len(results['dft_maes'])
    
    # Verify that the split structure was preserved
    assert len(results['semi_maes']) == 3


def test_train_models_empty_splits(temp_data_dir):
    """Test that train_models handles empty splits gracefully."""
    # Create dummy data
    n_samples = 100
    semi_path = os.path.join(temp_data_dir, "descriptors_semi.csv")
    dft_path = os.path.join(temp_data_dir, "descriptors_dft.csv")
    splits_path = os.path.join(temp_data_dir, "splits.json")
    
    # Generate dummy data
    semi_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples),
        'LUMO_energy': np.random.rand(n_samples),
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(semi_data).to_csv(semi_path, index=False)
    
    dft_data = {
        'molecule_id': [f"mol_{i}" for i in range(n_samples)],
        'HOMO_energy': np.random.rand(n_samples),
        'LUMO_energy': np.random.rand(n_samples),
        'mayer_bond_order': np.random.rand(n_samples)
    }
    pd.DataFrame(dft_data).to_csv(dft_path, index=False)
    
    # Create empty splits
    with open(splits_path, 'w') as f:
        json.dump([], f)
    
    # Run training - should return empty results
    logger = MockLogger()
    results = train_models(semi_path, dft_path, splits_path, logger=logger)
    
    # Verify empty results
    assert results['semi_maes'] == []
    assert results['dft_maes'] == []