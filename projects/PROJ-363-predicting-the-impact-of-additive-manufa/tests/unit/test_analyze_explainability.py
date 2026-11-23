import os
import sys
import tempfile
import json
import pickle
import pytest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analyze_explainability import find_best_model, calculate_shap_and_plot, load_model
from utils import setup_logging

class TestAnalyzeExplainability:
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup temporary directories for testing."""
        # Mock directory structure
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data" / "processed"
        self.model_dir = self.tmp_dir / "models" / "artifacts"
        self.report_dir = self.tmp_dir / "results" / "reports"
        self.plot_dir = self.tmp_dir / "results" / "plots"
        
        self.data_dir.mkdir(parents=True)
        self.model_dir.mkdir(parents=True)
        self.report_dir.mkdir(parents=True)
        self.plot_dir.mkdir(parents=True)

        # Create mock data
        self.mock_data = pd.DataFrame({
            'laser_power': [100, 200, 300, 400, 500],
            'scan_speed': [500, 600, 700, 800, 900],
            'hatch_spacing': [0.05, 0.06, 0.07, 0.08, 0.09],
            'layer_thickness': [0.03, 0.03, 0.03, 0.03, 0.03],
            'porosity': [0.01, 0.02, 0.015, 0.025, 0.03]
        })
        self.data_file = self.data_dir / "cleaned_316L.csv"
        self.mock_data.to_csv(self.data_file, index=False)

        # Create mock model
        self.mock_model = GradientBoostingRegressor(random_state=42)
        self.mock_model.fit(self.mock_data[['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']], 
                            self.mock_data['porosity'])
        self.model_file = self.model_dir / "gradient_boosting.pkl"
        with open(self.model_file, 'wb') as f:
            pickle.dump(self.mock_model, f)

        # Create mock metrics
        self.metrics = {
            "models": {
                "gradient_boosting": {
                    "mean_r2": 0.85,
                    "mean_rmse": 0.01
                },
                "mlp": {
                    "mean_r2": 0.80,
                    "mean_rmse": 0.015
                }
            }
        }
        self.metrics_file = self.report_dir / "model_metrics.json"
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f)

        # Patch the global paths in the module
        import code.analyze_explainability as mod
        mod.PROJECT_ROOT = self.tmp_dir
        mod.DATA_PATH = self.data_file
        mod.MODEL_PATH = self.model_dir
        mod.REPORTS_DIR = self.report_dir
        mod.PLOTS_DIR = self.plot_dir

    def test_find_best_model(self):
        """Test that find_best_model correctly identifies the best model."""
        path, name = find_best_model()
        assert name == "gradient_boosting"
        assert path == self.model_file
        assert path.exists()

    def test_calculate_shap_and_plot(self):
        """Test SHAP calculation and plot generation."""
        model = load_model(self.model_file)
        X = self.mock_data[['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']]
        
        plot_path = calculate_shap_and_plot(model, X, "gradient_boosting")
        
        assert plot_path.exists()
        assert plot_path.suffix == ".png"
        assert plot_path.parent == self.plot_dir
        assert plot_path.name == "shap_summary.png"

    def test_find_best_model_missing_metrics(self):
        """Test error handling when metrics file is missing."""
        self.metrics_file.unlink()
        with pytest.raises(FileNotFoundError):
            find_best_model()

    def test_find_best_model_missing_model_file(self):
        """Test error handling when model file is missing."""
        self.model_file.unlink()
        with pytest.raises(FileNotFoundError):
            find_best_model()
