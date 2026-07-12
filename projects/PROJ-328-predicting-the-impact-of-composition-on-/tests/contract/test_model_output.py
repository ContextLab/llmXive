"""
Contract test for model output schema (User Story 2).

This test verifies that the model training pipeline produces outputs
that strictly adhere to the expected schema defined in the project
specifications. It ensures:

1. Metrics file contains required keys (R2, RMSE, MAE, CV folds).
2. Feature importance file is present and contains valid data.
3. SHAP summary data exists and matches expected structure.
4. VIF diagnostics are present for collinearity checks.
5. Sensitivity analysis results are saved correctly.
"""
import os
import json
import pytest
import yaml
import pandas as pd
from pathlib import Path

# Import project configuration to get expected paths
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import (
    get_models_dir, 
    get_data_processed_dir, 
    get_data_outputs_dir,
    get_vif_threshold,
    get_r2_sensitivity_thresholds
)
from utils.error_handlers import ModelTrainingError

# Constants for schema validation
REQUIRED_METRIC_KEYS = {
    "model_type",
    "r2_score",
    "rmse",
    "mae",
    "cv_mean_r2",
    "cv_std_r2",
    "training_samples",
    "test_samples",
    "hyperparameters",
    "timestamp"
}

REQUIRED_VIF_KEYS = {
    "feature_name",
    "vif_score",
    "is_collinear"
}

REQUIRED_SHAP_KEYS = {
    "feature_name",
    "mean_abs_shap",
    "rank"
}

REQUIRED_SENSITIVITY_KEYS = {
    "threshold",
    "fraction_exceeding"
}

class TestModelOutputSchema:
    """
    Contract tests ensuring model artifacts adhere to the project schema.
    """

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        """Set up paths for test assertions."""
        self.models_dir = Path(get_models_dir())
        self.data_processed_dir = Path(get_data_processed_dir())
        self.outputs_dir = Path(get_data_outputs_dir())
        
        # Ensure directories exist (they should be created by T030)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def test_metrics_file_exists_and_has_required_keys(self):
        """
        Contract: Metrics JSON must exist and contain all required keys.
        Expected path: models/<model_name>_metrics.json
        """
        # Look for any metrics JSON file in the models directory
        metrics_files = list(self.models_dir.glob("*_metrics.json"))
        
        assert len(metrics_files) > 0, (
            "Contract Failed: No metrics file found in models directory. "
            "The training pipeline must save metrics to models/<model_name>_metrics.json"
        )
        
        # Validate the first found metrics file (or the most recent)
        metrics_file = sorted(metrics_files, key=lambda p: p.stat().st_mtime)[-1]
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        missing_keys = REQUIRED_METRIC_KEYS - set(metrics.keys())
        assert not missing_keys, (
            f"Contract Failed: Metrics file '{metrics_file.name}' is missing required keys: {missing_keys}"
        )

        # Validate specific value constraints
        assert isinstance(metrics['r2_score'], (int, float)), "r2_score must be numeric"
        assert isinstance(metrics['rmse'], (int, float)), "rmse must be numeric"
        assert metrics['training_samples'] > 0, "training_samples must be positive"
        
        # Check that VIF threshold is respected in metadata if present
        if 'vif_threshold' in metrics:
            assert metrics['vif_threshold'] == get_vif_threshold(), "VIF threshold mismatch"

    def test_feature_importance_file_exists(self):
        """
        Contract: Feature importance CSV must exist with correct columns.
        Expected path: models/<model_name>_feature_importance.csv
        """
        importance_files = list(self.models_dir.glob("*_feature_importance.csv"))
        
        assert len(importance_files) > 0, (
            "Contract Failed: No feature importance file found. "
            "The training pipeline must save importance to models/<model_name>_feature_importance.csv"
        )
        
        importance_file = sorted(importance_files, key=lambda p: p.stat().st_mtime)[-1]
        df = pd.read_csv(importance_file)
        
        required_columns = {'feature', 'importance', 'rank'}
        assert required_columns.issubset(df.columns), (
            f"Contract Failed: Feature importance file missing columns. "
            f"Expected: {required_columns}, Found: {set(df.columns)}"
        )
        
        # Validate data types
        assert df['importance'].dtype in ['float64', 'int64', 'float32'], "Importance must be numeric"
        assert df['rank'].dtype in ['int64', 'int32'], "Rank must be integer"

    def test_vif_diagnostics_exist(self):
        """
        Contract: VIF diagnostics must be saved for collinearity analysis.
        Expected path: models/<model_name>_vif_diagnostics.csv
        """
        vif_files = list(self.models_dir.glob("*_vif_diagnostics.csv"))
        
        assert len(vif_files) > 0, (
            "Contract Failed: No VIF diagnostics file found. "
            "The training pipeline must save VIF scores to models/<model_name>_vif_diagnostics.csv"
        )
        
        vif_file = sorted(vif_files, key=lambda p: p.stat().st_mtime)[-1]
        df = pd.read_csv(vif_file)
        
        required_columns = {'feature_name', 'vif_score', 'is_collinear'}
        assert required_columns.issubset(df.columns), (
            f"Contract Failed: VIF diagnostics missing columns. "
            f"Expected: {required_columns}, Found: {set(df.columns)}"
        )
        
        # Validate logic: is_collinear must be boolean and match vif_score >= threshold
        threshold = get_vif_threshold()
        expected_collinear = df['vif_score'] >= threshold
        assert all(df['is_collinear'] == expected_collinear), (
            "Contract Failed: is_collinear column does not match vif_score >= threshold logic"
        )

    def test_shap_analysis_exists(self):
        """
        Contract: SHAP analysis summary must exist with top features.
        Expected path: models/<model_name>_shap_summary.json or .csv
        """
        shap_json_files = list(self.models_dir.glob("*_shap_summary.json"))
        shap_csv_files = list(self.models_dir.glob("*_shap_summary.csv"))
        
        assert len(shap_json_files) > 0 or len(shap_csv_files) > 0, (
            "Contract Failed: No SHAP summary file found. "
            "The training pipeline must save SHAP analysis to models/<model_name>_shap_summary.{json,csv}"
        )
        
        # Prefer JSON for structured data
        if shap_json_files:
            shap_file = sorted(shap_json_files, key=lambda p: p.stat().st_mtime)[-1]
            with open(shap_file, 'r') as f:
                shap_data = json.load(f)
            
            # Ensure it's a list of top features
            assert isinstance(shap_data, list), "SHAP summary must be a list of features"
            if len(shap_data) > 0:
                missing_keys = REQUIRED_SHAP_KEYS - set(shap_data[0].keys())
                assert not missing_keys, (
                    f"Contract Failed: SHAP summary items missing keys: {missing_keys}"
                )
        else:
            shap_file = sorted(shap_csv_files, key=lambda p: p.stat().st_mtime)[-1]
            df = pd.read_csv(shap_file)
            assert 'feature_name' in df.columns, "SHAP summary must have feature_name column"
            assert 'mean_abs_shap' in df.columns, "SHAP summary must have mean_abs_shap column"

    def test_sensitivity_analysis_yaml_exists(self):
        """
        Contract: Sensitivity analysis results must be saved to data/processed/sensitivity_analysis.yaml.
        Per SC-005: Must contain fraction of bootstrap samples exceeding thresholds.
        """
        sensitivity_path = self.data_processed_dir / "sensitivity_analysis.yaml"
        
        assert sensitivity_path.exists(), (
            f"Contract Failed: Sensitivity analysis file missing at {sensitivity_path}. "
            "Per SC-005, this file must be generated."
        )
        
        with open(sensitivity_path, 'r') as f:
            sensitivity_data = yaml.safe_load(f)
        
        assert isinstance(sensitivity_data, list), "Sensitivity data must be a list of results"
        assert len(sensitivity_data) > 0, "Sensitivity data cannot be empty"
        
        # Validate structure against expected thresholds
        expected_thresholds = get_r2_sensitivity_thresholds()
        found_thresholds = [item['threshold'] for item in sensitivity_data]
        
        for thresh in expected_thresholds:
            assert thresh in found_thresholds, (
                f"Contract Failed: Sensitivity analysis missing threshold {thresh}. "
                f"Expected thresholds: {expected_thresholds}, Found: {found_thresholds}"
            )
        
        # Validate fraction field exists and is numeric
        for item in sensitivity_data:
            assert 'fraction_exceeding' in item, "Each sensitivity item must have 'fraction_exceeding'"
            assert isinstance(item['fraction_exceeding'], (int, float)), "fraction_exceeding must be numeric"
            assert 0.0 <= item['fraction_exceeding'] <= 1.0, "fraction_exceeding must be between 0 and 1"

    def test_model_artifact_is_pickleable(self):
        """
        Contract: The actual model artifact (e.g., .pkl or .joblib) must exist and be loadable.
        """
        # Look for common model artifact extensions
        artifact_files = list(self.models_dir.glob("*.pkl")) + list(self.models_dir.glob("*.joblib"))
        
        assert len(artifact_files) > 0, (
            "Contract Failed: No model artifact (.pkl or .joblib) found in models directory."
        )
        
        # Try to load the most recent one to ensure it's valid
        import joblib
        model_file = sorted(artifact_files, key=lambda p: p.stat().st_mtime)[-1]
        
        try:
            model = joblib.load(str(model_file))
            # Basic sanity check: model should have a predict method
            assert hasattr(model, 'predict'), "Loaded model artifact must have a 'predict' method"
        except Exception as e:
            pytest.fail(f"Contract Failed: Model artifact '{model_file}' could not be loaded: {e}")

    def test_no_fabricated_data_in_outputs(self):
        """
        Contract: Verify that outputs are not obviously fabricated.
        Checks for:
        1. R2 not exactly 1.0 (unless N=1, which is invalid for regression)
        2. RMSE not exactly 0.0
        3. VIF scores are not all 1.0 (perfect multicollinearity is rare in real data)
        """
        # Load metrics
        metrics_files = list(self.models_dir.glob("*_metrics.json"))
        if not metrics_files:
            pytest.skip("Metrics file not found, cannot verify data authenticity")
        
        metrics_file = sorted(metrics_files, key=lambda p: p.stat().st_mtime)[-1]
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        r2 = metrics.get('r2_score', 0)
        rmse = metrics.get('rmse', 0)
        
        # R2 of exactly 1.0 is highly suspicious for real experimental data
        assert r2 < 1.0, "Contract Warning: R2 score is exactly 1.0. This suggests fabricated or overfitted data."
        
        # RMSE of exactly 0.0 is highly suspicious
        assert rmse > 0.0, "Contract Warning: RMSE is exactly 0.0. This suggests fabricated data."

        # Load VIF diagnostics
        vif_files = list(self.models_dir.glob("*_vif_diagnostics.csv"))
        if vif_files:
            vif_file = sorted(vif_files, key=lambda p: p.stat().st_mtime)[-1]
            df = pd.read_csv(vif_file)
            
            # If all VIFs are 1.0, features are uncorrelated, which is unlikely for engineered descriptors
            # We don't fail, but we assert at least one is > 1.0 to be safe
            if len(df) > 1:
                max_vif = df['vif_score'].max()
                assert max_vif > 1.0, "Contract Warning: All VIF scores are 1.0. This suggests fabricated feature engineering."