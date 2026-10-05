import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from map import validate_map_against_independent_reports

class TestMapValidation:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure simulating the project."""
        temp_dir = tempfile.mkdtemp()
        data_dir = Path(temp_dir) / "data" / "processed"
        models_dir = Path(temp_dir) / "data" / "models"
        data_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a mock config file
        config_content = f"""
        PROJECT_ROOT = "{temp_dir}"
        """
        with open(Path(temp_dir) / "config.py", "w") as f:
            f.write(config_content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_unified_dataset(self, temp_project_root):
        """Create a mock unified dataset with bleaching labels."""
        data_path = Path(temp_project_root) / "data" / "processed" / "reef_species_unified.csv"
        df = pd.DataFrame({
            'reef_id': [1, 2, 3, 4, 5],
            'species_id': ['A', 'B', 'C', 'D', 'E'],
            'SST': [29.5, 30.1, 28.9, 31.0, 29.8],
            'DHW': [4.5, 5.2, 3.8, 6.1, 4.9],
            'thermal_tolerance': [2.0, 1.8, 2.2, 1.5, 1.9],
            'bleaching_label': [1, 1, 0, 1, 0], # Binary labels
            'trait_missing_flag': [0, 0, 0, 0, 0]
        })
        df.to_csv(data_path, index=False)
        return data_path

    @pytest.fixture
    def mock_model(self, temp_project_root):
        """Create a mock XGBoost model (or sklearn equivalent) for testing."""
        # We'll use a simple dummy classifier that returns consistent probabilities
        from sklearn.dummy import DummyClassifier
        import pickle
        
        model_path = Path(temp_project_root) / "data" / "models" / "xgboost_model.pkl"
        
        # Create a dummy model that predicts based on a simple rule
        model = DummyClassifier(strategy='stratified', random_state=42)
        # Fit on dummy data to make it valid
        X_dummy = np.array([[29.5, 4.5, 2.0], [30.1, 5.2, 1.8], [28.9, 3.8, 2.2]])
        y_dummy = np.array([1, 1, 0])
        model.fit(X_dummy, y_dummy)
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return model_path

    def test_validation_with_independent_data(self, temp_project_root, mock_unified_dataset, mock_model):
        """Test that validation computes AUPRC when data is available."""
        # Ensure config is importable
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", Path(temp_project_root) / "config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        # Mock the config import in map module
        import map as map_module
        map_module.config = config_module
        
        result = validate_map_against_independent_reports()
        
        assert result["independent_data_available"] is True
        assert result["auprc"] is not None
        assert isinstance(result["auprc"], float)
        
        # Verify file was written
        metrics_path = Path(temp_project_root) / "metrics.json"
        assert metrics_path.exists()
        
        with open(metrics_path, 'r') as f:
            saved_metrics = json.load(f)
        
        assert saved_metrics["independent_data_available"] is True
        assert saved_metrics["auprc"] is not None

    def test_validation_without_independent_data(self, temp_project_root):
        """Test that validation handles missing data gracefully."""
        # Ensure config is importable
        import importlib.util
        spec = importlib.util.spec_from_file_location("config", Path(temp_project_root) / "config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        
        import map as map_module
        map_module.config = config_module
        
        result = validate_map_against_independent_reports()
        
        assert result["independent_data_available"] is False
        assert result["auprc"] is None
        
        metrics_path = Path(temp_project_root) / "metrics.json"
        assert metrics_path.exists()
        
        with open(metrics_path, 'r') as f:
            saved_metrics = json.load(f)
        
        assert saved_metrics["independent_data_available"] is False
        assert saved_metrics["auprc"] is None