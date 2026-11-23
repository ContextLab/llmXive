import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.modeling.train import load_processed_data, train_model
from code.utils.constants import DATA_PROCESSED_DIR, RESULTS_DIR, N_ESTIMATORS, RANDOM_STATE, MAX_DEPTH_GRID

@pytest.fixture
def mock_processed_data(tmp_path):
    """Create mock processed data files for testing."""
    # Create directories
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock matrix
    n_samples = 100
    n_features = 10
    X = pd.DataFrame(
        np.random.rand(n_samples, n_features),
        columns=[f"metabolite_{i}" for i in range(n_features)],
        index=[f"sample_{i}" for i in range(n_samples)]
    )
    matrix_path = data_dir / "batch_corrected_matrix.csv"
    X.to_csv(matrix_path)
    
    # Mock labels
    y = pd.Series(
        np.random.randint(0, 2, n_samples),
        name="binary_label",
        index=X.index
    )
    labels_path = data_dir / "labels.csv"
    y.to_frame().to_csv(labels_path)
    
    # Mock split indices (optional for this test, but good to have)
    split_path = data_dir / "split_indices.json"
    with open(split_path, 'w') as f:
        json.dump({"train_indices": list(range(80)), "holdout_indices": list(range(80, 100))}, f)
    
    return data_dir

def test_load_processed_data(mock_processed_data):
    """Test that load_processed_data correctly loads the mock files."""
    # Temporarily override DATA_PROCESSED_DIR
    original_dir = DATA_PROCESSED_DIR
    DATA_PROCESSED_DIR = mock_processed_data
    
    try:
        X, y, features = load_processed_data()
        assert X.shape[0] == 100
        assert X.shape[1] == 10
        assert len(y) == 100
        assert len(features) == 10
    finally:
        DATA_PROCESSED_DIR = original_dir

def test_train_model_structure(mock_processed_data):
    """Test that train_model returns a valid model and results."""
    # Override DATA_PROCESSED_DIR
    original_dir = DATA_PROCESSED_DIR
    DATA_PROCESSED_DIR = mock_processed_data
    
    try:
        X, y, features = load_processed_data()
        
        # Train with minimal grid to speed up test
        # We can't easily override the global constants in the function, 
        # so we rely on the function using the constants as defined.
        # Since N_ESTIMATORS=500, this might be slow, so we test the logic flow.
        # For a unit test, we might want to mock the GridSearch or use a smaller grid.
        # However, the task requires using N_ESTIMATORS from constants.
        # We will trust the logic and just check the return types.
        
        model, results = train_model(X, y, features)
        
        assert isinstance(model, RandomForestClassifier)
        assert model.n_estimators == N_ESTIMATORS
        assert model.random_state == RANDOM_STATE
        assert 'best_score_' in results
        assert 'params' in results
    finally:
        DATA_PROCESSED_DIR = original_dir
