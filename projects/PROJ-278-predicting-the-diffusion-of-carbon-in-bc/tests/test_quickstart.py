import pytest
import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import load_config, get_path
from exceptions import DataInsufficientError

class TestQuickstartValidation:
    """
    T024 Validation Tests.
    These tests verify that the full pipeline (01_download -> 04_evaluate)
    produces valid outputs matching the schemas and requirements.
    """

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def paths(self, config):
        return {
            "cleaned_data": get_path(config, "data_path", "processed") / "dataset_cleaned.csv",
            "model_results": get_path(config, "output_path", "outputs") / "model_results.json",
            "feature_importance": get_path(config, "output_path", "outputs") / "feature_importance.json",
            "variance_partition": get_path(config, "output_path", "outputs") / "variance_partition.csv",
            "best_model": get_path(config, "output_path", "outputs") / "best_model.pkl",
            "baseline_model": get_path(config, "output_path", "outputs") / "baseline_model.pkl",
        }

    def test_pipeline_outputs_exist(self, paths):
        """Verify all expected output files exist after pipeline run."""
        for name, path in paths.items():
            assert path.exists(), f"Expected output file {name} not found at {path}"

    def test_dataset_schema_compliance(self, paths, config):
        """Verify dataset_cleaned.csv matches the schema defined in T004."""
        schema_path = PROJECT_ROOT / "specs" / "001-predict-carbon-diffusion-bcc" / "contracts" / "dataset.schema.yaml"
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        df = pd.read_csv(paths["cleaned_data"])
        
        # Check columns
        required_cols = list(schema.get('properties', {}).keys())
        for col in required_cols:
            assert col in df.columns, f"Missing column in dataset: {col}"

    def test_model_results_schema_compliance(self, paths):
        """Verify model_results.json matches the schema defined in T005."""
        schema_path = PROJECT_ROOT / "specs" / "001-predict-carbon-diffusion-bcc" / "contracts" / "model_output.schema.yaml"
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        with open(paths["model_results"], 'r') as f:
            data = json.load(f)
        
        required_keys = schema.get('required', [])
        for key in required_keys:
            assert key in data, f"Missing key in model_results.json: {key}"

    def test_feature_importance_structure(self, paths):
        """Verify feature_importance.json has required structure."""
        with open(paths["feature_importance"], 'r') as f:
            data = json.load(f)
        
        assert "ranked_features" in data, "Missing 'ranked_features' in feature_importance.json"
        assert "top_two" in data, "Missing 'top_two' in feature_importance.json"
        assert isinstance(data["ranked_features"], list), "ranked_features must be a list"
        assert len(data["top_two"]) == 2, "top_two must contain exactly 2 items"

    def test_variance_partition_structure(self, paths):
        """Verify variance_partition.csv has required columns."""
        df = pd.read_csv(paths["variance_partition"])
        required_cols = ["adjusted_r2", "microstructural_gap", "residual_variance_label"]
        
        for col in required_cols:
            assert col in df.columns, f"Missing column in variance_partition.csv: {col}"
        
        # Check that values are reasonable (0 <= R2 <= 1)
        assert 0 <= df["adjusted_r2"].iloc[0] <= 1, "adjusted_r2 must be between 0 and 1"
        assert 0 <= df["microstructural_gap"].iloc[0] <= 1, "microstructural_gap must be between 0 and 1"

    def test_models_are_pickleable(self, paths):
        """Verify model files are valid pickle objects."""
        import pickle
        
        with open(paths["best_model"], 'rb') as f:
            model = pickle.load(f)
        assert model is not None, "Best model could not be loaded"
        
        with open(paths["baseline_model"], 'rb') as f:
            baseline = pickle.load(f)
        assert baseline is not None, "Baseline model could not be loaded"
