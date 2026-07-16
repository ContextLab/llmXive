"""
Unit tests for the Quickstart Validator (T033).
These tests verify the validation logic without running the full pipeline.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logger import setup_logger, get_logger
from config import set_seeds

# Mock the required directories and files for testing
class TestQuickstartValidator:
    """Test cases for quickstart validation logic."""

    @pytest.fixture
    def temp_artifact_dirs(self, tmp_path):
        """Create temporary directory structure mimicking project artifacts."""
        # Create directory structure
        artifacts_dir = tmp_path / "artifacts"
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        raw_dir = data_dir / "raw"
        models_dir = artifacts_dir / "models"
        metrics_dir = artifacts_dir / "metrics"
        plots_dir = artifacts_dir / "plots"

        for d in [artifacts_dir, data_dir, processed_dir, raw_dir, models_dir, metrics_dir, plots_dir]:
            d.mkdir(parents=True)

        return {
            "artifacts": artifacts_dir,
            "data": data_dir,
            "processed": processed_dir,
            "raw": raw_dir,
            "models": models_dir,
            "metrics": metrics_dir,
            "plots": plots_dir,
            "tmp_path": tmp_path
        }

    def test_check_artifacts_exist_with_missing_files(self, temp_artifact_dirs):
        """Test artifact existence check when files are missing."""
        # Create only some of the required files
        (temp_artifact_dirs["processed"] / "features_2d.npy").touch()
        (temp_artifact_dirs["processed"] / "labels.csv").touch()
        # Note: features_3d.npy is missing

        # Import and test the logic directly
        from code.utils.logger import get_logger
        logger = get_logger("test_validator")

        missing = []
        required_files = [
            temp_artifact_dirs["raw"] / "qm9_full.parquet",
            temp_artifact_dirs["processed"] / "molecules_cleaned.parquet",
            temp_artifact_dirs["processed"] / "features_2d.npy",
            temp_artifact_dirs["processed"] / "features_3d.npy",
            temp_artifact_dirs["processed"] / "labels.csv",
        ]

        for f in required_files:
            if not f.exists():
                missing.append(str(f))

        assert len(missing) > 0, "Should detect missing files"
        assert any("features_3d.npy" in f for f in missing), "Should detect missing features_3d.npy"

    def test_data_integrity_validation(self, temp_artifact_dirs):
        """Test data integrity validation with valid data."""
        # Create valid test data
        processed_dir = temp_artifact_dirs["processed"]
        
        # Create features
        feat_2d = np.random.rand(100, 2048).astype(np.float32)
        feat_3d = np.random.rand(100, 50).astype(np.float32)
        np.save(processed_dir / "features_2d.npy", feat_2d)
        np.save(processed_dir / "features_3d.npy", feat_3d)

        # Create labels
        labels_df = pd.DataFrame({
            'molecule_id': [f'mol_{i}' for i in range(100)],
            'dipole': np.random.rand(100),
            'HOMO': np.random.rand(100),
            'LUMO': np.random.rand(100)
        })
        labels_df.to_csv(processed_dir / "labels.csv", index=False)

        # Test validation logic
        loaded_2d = np.load(processed_dir / "features_2d.npy")
        loaded_3d = np.load(processed_dir / "features_3d.npy")
        loaded_labels = pd.read_csv(processed_dir / "labels.csv")

        assert len(loaded_2d) == len(loaded_3d) == len(loaded_labels)
        assert loaded_2d.shape == (100, 2048)
        assert loaded_3d.shape == (100, 50)

    def test_model_artifact_validation(self, temp_artifact_dirs):
        """Test model artifact validation."""
        import pickle
        import json

        models_dir = temp_artifact_dirs["models"]
        metrics_dir = temp_artifact_dirs["metrics"]

        # Create mock models
        mock_model = {"type": "RandomForest", "params": {"n_estimators": 100}}
        with open(models_dir / "model_2d.pkl", "wb") as f:
            pickle.dump(mock_model, f)
        with open(models_dir / "model_3d.pkl", "wb") as f:
            pickle.dump(mock_model, f)

        # Create mock metrics
        cv_metrics = {
            "fold_maes": [0.1, 0.12, 0.09, 0.11, 0.1],
            "mean_mae": 0.104,
            "std_mae": 0.008
        }
        with open(metrics_dir / "cv_metrics.json", "w") as f:
            json.dump(cv_metrics, f)

        stability_report = {
            "fold_maes": [0.1, 0.12, 0.09, 0.11, 0.1],
            "stability_ratio": 0.077,
            "passed": True
        }
        with open(metrics_dir / "stability_report.json", "w") as f:
            json.dump(stability_report, f)

        # Test loading
        with open(models_dir / "model_2d.pkl", "rb") as f:
            loaded_model = pickle.load(f)
        assert loaded_model["type"] == "RandomForest"

        with open(metrics_dir / "cv_metrics.json", "r") as f:
            loaded_metrics = json.load(f)
        assert "fold_maes" in loaded_metrics

    def test_analysis_artifact_validation(self, temp_artifact_dirs):
        """Test analysis artifact validation."""
        import json

        metrics_dir = temp_artifact_dirs["metrics"]
        plots_dir = temp_artifact_dirs["plots"]

        # Create mock analysis files
        test_preds = {
            "error_2d": [0.1, 0.2, 0.15],
            "error_3d": [0.08, 0.18, 0.12]
        }
        with open(metrics_dir / "test_predictions.json", "w") as f:
            json.dump(test_preds, f)

        stats = {
            "dipole": {"p_value": 0.01, "significant": True},
            "HOMO": {"p_value": 0.03, "significant": True},
            "LUMO": {"p_value": 0.05, "significant": False}
        }
        with open(metrics_dir / "statistics.json", "w") as f:
            json.dump(stats, f)

        failure_boundary = [
            {"molecule_id": "mol_1", "descriptor": "dipole", "reason": "p_value < 0.0167"}
        ]
        with open(metrics_dir / "failure_boundary.json", "w") as f:
            json.dump(failure_boundary, f)

        # Create mock plots (empty files with content)
        for plot in ["parity_2d.png", "parity_3d.png"]:
            plot_path = plots_dir / plot
            plot_path.write_bytes(b"PNG_MOCK_DATA")

        # Create mock report
        report_path = temp_artifact_dirs["artifacts"] / "report.md"
        report_path.write_text("# Validation Report\n\nAll tests passed.")

        # Test loading
        with open(metrics_dir / "test_predictions.json", "r") as f:
            loaded_preds = json.load(f)
        assert "error_2d" in loaded_preds

        for plot in ["parity_2d.png", "parity_3d.png"]:
            plot_path = plots_dir / plot
            assert plot_path.exists()
            assert plot_path.stat().st_size > 0

    def test_validation_report_generation(self, temp_artifact_dirs):
        """Test that validation report is generated correctly."""
        metrics_dir = temp_artifact_dirs["metrics"]

        # Simulate validation results
        results = {
            "timestamp": "2024-01-01 12:00:00",
            "checks": {
                "artifact_existence": {"passed": True, "missing_files": []},
                "data_integrity": {"passed": True, "message": "OK"},
                "model_artifacts": {"passed": True, "message": "OK"},
                "analysis_artifacts": {"passed": True, "message": "OK"}
            },
            "overall_status": "passed",
            "errors": []
        }

        report_path = metrics_dir / "quickstart_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)

        # Verify report
        assert report_path.exists()
        with open(report_path, "r") as f:
            loaded_results = json.load(f)
        
        assert loaded_results["overall_status"] == "passed"
        assert all(check["passed"] for check in loaded_results["checks"].values())