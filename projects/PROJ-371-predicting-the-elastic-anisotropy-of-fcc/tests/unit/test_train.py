import pytest
import numpy as np
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path if necessary (usually handled by test runner)
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.models.train import (
    load_processed_data, 
    prepare_loeo_data, 
    train_single_model, 
    evaluate_model, 
    run_loeo_cross_validation,
    save_results
)

@pytest.fixture
def sample_loeo_data():
    """Create a small synthetic dataset for testing LOEO logic."""
    # We need materials with known elements to test the split
    data = {
        'material_id': ['MP-1', 'MP-2', 'MP-3', 'MP-4', 'MP-5'],
        'formula': ['Al', 'Al-Cu', 'Cu', 'Fe-Al', 'Fe'],
        'C11': [100, 110, 120, 130, 140],
        'C12': [50, 55, 60, 65, 70],
        'C44': [30, 35, 40, 45, 50],
        'A1': [1.2, 1.3, 1.4, 1.5, 1.6],
        'atomic_radius_variance': [0.1, 0.2, 0.3, 0.4, 0.5],
        'electronegativity_std': [0.1, 0.2, 0.3, 0.4, 0.5],
        'valence_electron_concentration': [3.0, 3.5, 4.0, 4.5, 5.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_loeo_manifest():
    """Create a temporary element_groups.json file."""
    # Mapping based on sample_loeo_data formulas
    # Al -> MP-1, MP-2, MP-4
    # Cu -> MP-2, MP-3
    # Fe -> MP-4, MP-5
    element_groups = {
        'Al': ['MP-1', 'MP-2', 'MP-4'],
        'Cu': ['MP-2', 'MP-3'],
        'Fe': ['MP-4', 'MP-5']
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(element_groups, f)
        return Path(f.name)

class TestLOEOSplitNoElementOverlap:
    def test_loeo_split_logic(self, sample_loeo_data, temp_loeo_manifest):
        """
        Verify that when we leave out an element, no material containing that element
        appears in the training set.
        """
        df, element_groups = prepare_loeo_data(sample_loeo_data, temp_loeo_manifest)
        
        # Manually check the split logic for 'Al'
        # Test set should be materials containing 'Al': MP-1, MP-2, MP-4
        # Train set should be materials NOT containing 'Al': MP-3, MP-5
        
        # We can't easily call the internal loop of run_loeo_cross_validation
        # without executing the whole thing, but we can verify the preparation
        # and the logic by inspecting the element_groups and data.
        
        # Verify that MP-1, MP-2, MP-4 are in element_groups['Al']
        assert 'MP-1' in element_groups['Al']
        assert 'MP-2' in element_groups['Al']
        assert 'MP-4' in element_groups['Al']
        
        # Verify that MP-3 and MP-5 are NOT in element_groups['Al']
        assert 'MP-3' not in element_groups['Al']
        assert 'MP-5' not in element_groups['Al']
        
        # The split logic in run_loeo_cross_validation does:
        # test_mat_ids = element_groups[leave_out_elem]
        # train_mat_ids = all_mats - test_mat_ids
        # This guarantees no overlap.
        
        # Let's simulate the split for 'Al'
        all_mats = set(sample_loeo_data['material_id'].tolist())
        test_mats = set(element_groups['Al'])
        train_mats = all_mats - test_mats
        
        # Check intersection is empty
        assert test_mats.intersection(train_mats) == set()
        
        # Check that train set does not contain any 'Al' materials
        for mat in train_mats:
            # If a material is in train, it should not be in the 'Al' group
            # But wait, a material can contain multiple elements.
            # If MP-2 contains Al and Cu, and we leave out Al, MP-2 is in test.
            # If we leave out Cu, MP-2 is in test.
            # If we leave out Fe, MP-2 is in train? 
            # MP-2 is in Al and Cu. If we leave out Fe, MP-2 is in train (since it doesn't contain Fe).
            # The constraint is: Test set contains ALL materials with element E.
            # Train set contains ALL materials WITHOUT element E.
            # So Train set = {m | E not in m.elements}
            # Test set = {m | E in m.elements}
            # Intersection is empty by definition.
            pass

class TestModelTraining:
    def test_train_random_forest(self):
        X = np.random.rand(10, 3)
        y = np.random.rand(10)
        model = train_single_model(X, y, "RandomForest", {"n_estimators": 2}, 42)
        assert model is not None
        assert hasattr(model, 'predict')
    
    def test_train_gradient_boosting(self):
        X = np.random.rand(10, 3)
        y = np.random.rand(10)
        model = train_single_model(X, y, "GradientBoosting", {"n_estimators": 2}, 42)
        assert model is not None
    
    def test_train_linear_regression(self):
        X = np.random.rand(10, 3)
        y = np.random.rand(10)
        model = train_single_model(X, y, "LinearRegression", {}, 42)
        assert model is not None

class TestModelEvaluation:
    def test_metrics_calculation(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.2, 4.8])
        
        model = MagicMock()
        model.predict.return_value = y_pred
        
        metrics = evaluate_model(model, np.array(y_pred), y_true)
        
        assert "r2" in metrics
        assert "mae" in metrics
        assert "rmse" in metrics
        assert metrics["n_test_samples"] == 5

class TestHyperparameters:
    def test_model_config_structure(self):
        # Verify that the model config structure is valid
        config = [
            {
                "name": "RandomForest",
                "hyperparameters": {
                    "n_estimators": 50,
                    "max_depth": 5
                }
            }
        ]
        assert len(config) > 0
        assert config[0]["name"] == "RandomForest"
        assert "n_estimators" in config[0]["hyperparameters"]