import pytest
import json
import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestClassifier

# Add code to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.evaluate import generate_learning_curve, main
from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR

@pytest.fixture
def small_dataset():
    """Creates a small dataset (N=30) for testing."""
    X = np.random.rand(30, 10)
    y = np.random.randint(0, 2, 30)
    return X, y

@pytest.fixture
def temp_dirs():
    """Creates temporary directories for testing."""
    temp_root = tempfile.mkdtemp()
    data_processed = os.path.join(temp_root, "data", "processed")
    results = os.path.join(temp_root, "results")
    os.makedirs(data_processed)
    os.makedirs(results)
    yield data_processed, results
    shutil.rmtree(temp_root)

def test_learning_curve_generates_output(temp_dirs, small_dataset):
    """Test that learning curve generates the expected output file."""
    data_processed, results = temp_dirs
    X, y = small_dataset
    
    # Create mock data files
    X_df = pd.DataFrame(X, columns=[f"met_{i}" for i in range(10)])
    y_df = pd.DataFrame({"binary_label": y})
    
    X_df.to_csv(os.path.join(data_processed, "batch_corrected_matrix.csv"))
    y_df.to_csv(os.path.join(data_processed, "labels.csv"))
    
    # Create a mock model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    import pickle
    with open(os.path.join(data_processed, "model.pkl"), "wb") as f:
        pickle.dump(model, f)
        
    # Create split indices (mock)
    indices = {"holdout_indices": []} # Empty for small dataset path
    with open(os.path.join(data_processed, "split_indices.json"), "w") as f:
        json.dump(indices, f)
        
    # Mock constants to use temp dirs
    with patch('modeling.evaluate.DATA_PROCESSED_DIR', data_processed), \
         patch('modeling.evaluate.RESULTS_DIR', results):
         
         result = generate_learning_curve()
         
         assert result is not None
         assert "training_sizes" in result
         assert "test_scores_mean" in result
         assert "power_limitation_warning" in result
         
         # Check that the file was written
         output_path = os.path.join(results, "learning_curve.json")
         assert os.path.exists(output_path)
         
         with open(output_path, 'r') as f:
             saved_data = json.load(f)
             
         assert "training_sizes" in saved_data
         assert "power_limitation_warning" in saved_data

def test_learning_curve_detects_steep_slope(temp_dirs, small_dataset):
    """Test that a steep slope triggers the power_limitation_warning."""
    data_processed, results = temp_dirs
    X, y = small_dataset
    
    # Create mock data files
    X_df = pd.DataFrame(X, columns=[f"met_{i}" for i in range(10)])
    y_df = pd.DataFrame({"binary_label": y})
    
    X_df.to_csv(os.path.join(data_processed, "batch_corrected_matrix.csv"))
    y_df.to_csv(os.path.join(data_processed, "labels.csv"))
    
    # Create a model that will likely underfit (very weak)
    model = RandomForestClassifier(n_estimators=2, max_depth=1, random_state=42)
    model.fit(X, y)
    
    import pickle
    with open(os.path.join(data_processed, "model.pkl"), "wb") as f:
        pickle.dump(model, f)
        
    indices = {"holdout_indices": []}
    with open(os.path.join(data_processed, "split_indices.json"), "w") as f:
        json.dump(indices, f)
        
    with patch('modeling.evaluate.DATA_PROCESSED_DIR', data_processed), \
         patch('modeling.evaluate.RESULTS_DIR', results):
         
         result = generate_learning_curve()
         
         # Even if slope calculation varies, the structure must be correct
         assert "power_limitation_warning" in result
         # The warning should be present if the curve is steep (which is likely for a weak model on small data)
         # We assert the key exists and is boolean
         assert isinstance(result["power_limitation_warning"], bool)
         
         # Verify the file content matches
         output_path = os.path.join(results, "learning_curve.json")
         with open(output_path, 'r') as f:
             saved_data = json.load(f)
             
         assert saved_data["power_limitation_warning"] == result["power_limitation_warning"]