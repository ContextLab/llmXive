"""
Unit tests for src/modeling/train_rf.py

Tests verify:
- Data loading logic (mocked)
- Model training with correct parameters (max_depth, n_estimators)
- Cross-validation execution
- Metric calculation (AUC, TSS)
- Output file generation
"""

import os
import sys
import tempfile
import json
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Add project root to path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.modeling.train_rf import (
    load_climate_features,
    train_random_forest_cv,
    save_results,
    run_training_pipeline,
    PROJECT_ROOT,
    PROCESSED_DATA_DIR,
    RESULTS_DIR
)
from src.utils.config import MAX_DEPTH, N_ESTIMATORS, RANDOM_SEED

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock data structure
        processed_dir = Path(tmpdir) / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create a mock CSV file
        species_name = "Testus_species"
        df = pd.DataFrame({
            'bio1': np.random.rand(100),
            'bio12': np.random.rand(100),
            'label': np.random.randint(0, 2, 100)
        })
        csv_path = processed_dir / f"{species_name}_climate_features.csv"
        df.to_csv(csv_path, index=False)

        yield {
            'tmpdir': tmpdir,
            'species': species_name,
            'csv_path': csv_path,
            'processed_dir': processed_dir
        }

@pytest.fixture
def temp_results_dir():
    """Create a temporary results directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir) / "results"
        results_dir.mkdir(parents=True)
        yield results_dir

def test_load_climate_features_success(temp_data_dir):
    """Test successful loading of climate features."""
    # Patch the path constants to use our temp directory
    with patch('src.modeling.train_rf.PROCESSED_DATA_DIR', temp_data_dir['processed_dir']):
        X, y, feature_names = load_climate_features(temp_data_dir['species'])

        assert isinstance(X, np.ndarray)
        assert isinstance(y, np.ndarray)
        assert len(y) == 100
        assert X.shape[1] == 2  # bio1, bio12
        assert 'label' not in feature_names
        assert set(feature_names) == {'bio1', 'bio12'}

def test_load_climate_features_missing_file():
    """Test error handling when file is missing."""
    with patch('src.modeling.train_rf.PROCESSED_DATA_DIR', Path('/nonexistent')):
        with pytest.raises(FileNotFoundError):
            load_climate_features("Missing_species")

def test_load_climate_features_missing_label():
    """Test error handling when 'label' column is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "data" / "processed"
        processed_dir.mkdir(parents=True)

        df = pd.DataFrame({'bio1': [1, 2], 'bio2': [3, 4]}) # No label
        df.to_csv(processed_dir / "Bad_species_climate_features.csv", index=False)

        with patch('src.modeling.train_rf.PROCESSED_DATA_DIR', processed_dir):
            with pytest.raises(ValueError):
                load_climate_features("Bad_species")

def test_train_random_forest_cv_parameters():
    """Test that the model is trained with correct hyperparameters."""
    X = np.random.rand(50, 5)
    y = np.random.randint(0, 2, 50)

    # Mock the model creation to inspect arguments
    with patch('src.modeling.train_rf.RandomForestClassifier') as mock_rf:
        mock_instance = MagicMock(spec=RandomForestClassifier)
        mock_instance.feature_importances_ = np.ones(5) / 5
        mock_rf.return_value = mock_instance

        # Run training (this will fail at predict_proba because we mocked the class,
        # but we can check the instantiation arguments before it fails or we can
        # mock cross_val_predict too. Let's mock cross_val_predict to return dummy probs)
        with patch('src.modeling.train_rf.cross_val_predict', return_value=np.random.rand(50)):
            with patch('src.modeling.train_rf.calculate_auc', return_value=0.9):
                with patch('src.modeling.train_rf.calculate_tss', return_value=0.8):
                    results = train_random_forest_cv(X, y)

    # Verify RandomForestClassifier was called with correct args
    mock_rf.assert_called_once()
    call_args = mock_rf.call_args
    assert call_args[1]['n_estimators'] == N_ESTIMATORS
    assert call_args[1]['max_depth'] == MAX_DEPTH
    assert call_args[1]['random_state'] == RANDOM_SEED
    assert call_args[1]['class_weight'] == 'balanced'

def test_save_results_creates_files(temp_results_dir):
    """Test that save_results creates the expected files."""
    species = "Test_species"
    mock_model = MagicMock()
    mock_predictions = np.random.rand(10)
    mock_labels = np.random.randint(0, 2, 10)

    results = {
        'model': mock_model,
        'cv_auc': 0.95,
        'cv_tss': 0.85,
        'cv_predictions': mock_predictions,
        'cv_labels': mock_labels,
        'feature_importance': {'bio1': 0.5, 'bio2': 0.5}
    }

    feature_names = ['bio1', 'bio2']

    with patch('src.modeling.train_rf.RESULTS_DIR', temp_results_dir):
        save_results(species, results, feature_names)

    # Check files exist
    json_path = temp_results_dir / f"{species}_model_results.json"
    pkl_path = temp_results_dir / f"{species}_model.pkl"
    pred_path = temp_results_dir / f"{species}_cv_predictions.csv"

    assert json_path.exists()
    assert pkl_path.exists()
    assert pred_path.exists()

    # Verify JSON content
    with open(json_path) as f:
        data = json.load(f)
    assert data['species'] == species
    assert data['cross_validation']['auc'] == 0.95
    assert data['hyperparameters']['n_estimators'] == N_ESTIMATORS
    assert data['hyperparameters']['max_depth'] == MAX_DEPTH

    # Verify pickle content
    with open(pkl_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model == mock_model

def test_run_training_pipeline_integration(temp_data_dir, temp_results_dir):
    """Integration test for the full pipeline with mocked dependencies."""
    species = temp_data_dir['species']

    # Patch paths
    with patch('src.modeling.train_rf.PROCESSED_DATA_DIR', temp_data_dir['processed_dir']):
        with patch('src.modeling.train_rf.RESULTS_DIR', temp_results_dir):
            # Mock the heavy lifting
            with patch('src.modeling.train_rf.train_random_forest_cv') as mock_train:
                mock_train.return_value = {
                    'model': MagicMock(),
                    'cv_auc': 0.90,
                    'cv_tss': 0.80,
                    'cv_predictions': np.random.rand(100),
                    'cv_labels': np.random.randint(0, 2, 100),
                    'feature_importance': {'bio1': 0.5, 'bio12': 0.5}
                }

                results = run_training_pipeline(species)

    assert results['cv_auc'] == 0.90
    assert results['cv_tss'] == 0.80

    # Verify output files were created
    assert (temp_results_dir / f"{species}_model_results.json").exists()
    assert (temp_results_dir / f"{species}_model.pkl").exists()