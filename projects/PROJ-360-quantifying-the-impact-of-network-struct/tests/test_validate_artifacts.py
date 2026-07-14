"""
Tests for T028 artifact validation.
These tests verify that the validation logic works correctly.
"""
import os
import sys
import json
import csv
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path to import validate_artifacts
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from validate_artifacts import (
    check_csv_artifact,
    check_json_artifact,
    check_text_artifact,
    REQUIRED_METRICS_COLUMNS,
    REQUIRED_CORRELATION_KEYS,
    REQUIRED_MODEL_KEYS,
    MANDATORY_LIMITATIONS_TEXT
)

class TestCSVValidation:
    def test_check_csv_artifact_exists_and_valid(self, tmp_path):
        """Test that a valid CSV passes validation."""
        csv_path = tmp_path / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_METRICS_COLUMNS)
            writer.writeheader()
            writer.writerow({col: "value" for col in REQUIRED_METRICS_COLUMNS})
        
        valid, msg = check_csv_artifact(csv_path, REQUIRED_METRICS_COLUMNS)
        assert valid is True
        assert "Valid CSV" in msg

    def test_check_csv_artifact_missing_file(self, tmp_path):
        """Test that a missing file fails validation."""
        csv_path = tmp_path / "nonexistent.csv"
        valid, msg = check_csv_artifact(csv_path, REQUIRED_METRICS_COLUMNS)
        assert valid is False
        assert "does not exist" in msg

    def test_check_csv_artifact_empty_file(self, tmp_path):
        """Test that an empty file fails validation."""
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        valid, msg = check_csv_artifact(csv_path, REQUIRED_METRICS_COLUMNS)
        assert valid is False
        assert "empty" in msg

    def test_check_csv_artifact_missing_columns(self, tmp_path):
        """Test that a CSV with missing columns fails validation."""
        csv_path = tmp_path / "incomplete.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id", "average_degree"])
            writer.writeheader()
            writer.writerow({"material_id": "1", "average_degree": "2.5"})
        
        valid, msg = check_csv_artifact(csv_path, REQUIRED_METRICS_COLUMNS)
        assert valid is False
        assert "Missing columns" in msg

class TestJSONValidation:
    def test_check_json_artifact_valid(self, tmp_path):
        """Test that a valid JSON passes validation."""
        json_path = tmp_path / "test.json"
        data = {key: {"test": "value"} for key in REQUIRED_CORRELATION_KEYS}
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        valid, msg = check_json_artifact(json_path, REQUIRED_CORRELATION_KEYS, is_nested=True)
        assert valid is True
        assert "Valid JSON" in msg

    def test_check_json_artifact_missing_file(self, tmp_path):
        """Test that a missing JSON file fails validation."""
        json_path = tmp_path / "nonexistent.json"
        valid, msg = check_json_artifact(json_path, REQUIRED_CORRELATION_KEYS, is_nested=True)
        assert valid is False
        assert "does not exist" in msg

    def test_check_json_artifact_invalid_json(self, tmp_path):
        """Test that invalid JSON fails validation."""
        json_path = tmp_path / "invalid.json"
        with open(json_path, 'w') as f:
            f.write("{ invalid json }")
        
        valid, msg = check_json_artifact(json_path, REQUIRED_CORRELATION_KEYS, is_nested=True)
        assert valid is False
        assert "Invalid JSON" in msg

    def test_check_json_artifact_missing_keys(self, tmp_path):
        """Test that JSON with missing keys fails validation."""
        json_path = tmp_path / "incomplete.json"
        with open(json_path, 'w') as f:
            json.dump({"only_one_key": "value"}, f)
        
        valid, msg = check_json_artifact(json_path, REQUIRED_CORRELATION_KEYS, is_nested=True)
        assert valid is False
        assert "Missing" in msg

class TestTextValidation:
    def test_check_text_artifact_valid(self, tmp_path):
        """Test that a valid text file passes validation."""
        txt_path = tmp_path / "test.txt"
        with open(txt_path, 'w') as f:
            f.write("Some content here")
        
        valid, msg = check_text_artifact(txt_path)
        assert valid is True
        assert "Valid text" in msg

    def test_check_text_artifact_missing_required_text(self, tmp_path):
        """Test that text without required content fails validation."""
        txt_path = tmp_path / "test.txt"
        with open(txt_path, 'w') as f:
            f.write("Some content without required text")
        
        valid, msg = check_text_artifact(txt_path, required_text="required text here")
        assert valid is False
        assert "Missing required text" in msg

    def test_check_text_artifact_contains_required_text(self, tmp_path):
        """Test that text with required content passes validation."""
        txt_path = tmp_path / "test.txt"
        with open(txt_path, 'w') as f:
            f.write(f"This is a report.\n{MANDATORY_LIMITATIONS_TEXT}\nEnd of report.")
        
        valid, msg = check_text_artifact(txt_path, required_text=MANDATORY_LIMITATIONS_TEXT)
        assert valid is True
        assert "Valid text" in msg

    def test_check_text_artifact_missing_file(self, tmp_path):
        """Test that a missing text file fails validation."""
        txt_path = tmp_path / "nonexistent.txt"
        valid, msg = check_text_artifact(txt_path)
        assert valid is False
        assert "does not exist" in msg

class TestIntegration:
    def test_main_validation_flow(self, tmp_path, monkeypatch):
        """Test that main() runs without crashing and returns appropriate exit code."""
        # Create a minimal valid structure in tmp_path
        data_processed = tmp_path / "data" / "processed"
        results_dir = tmp_path / "results"
        models_dir = tmp_path / "models"
        
        data_processed.mkdir(parents=True)
        results_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        
        # Create a minimal valid metrics.csv
        metrics_csv = data_processed / "metrics.csv"
        with open(metrics_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_METRICS_COLUMNS)
            writer.writeheader()
            writer.writerow({col: "value" for col in REQUIRED_METRICS_COLUMNS})
        
        # Create a minimal valid correlations.json
        correlations_json = results_dir / "correlations.json"
        with open(correlations_json, 'w') as f:
            json.dump({key: {"test": 1.0} for key in REQUIRED_CORRELATION_KEYS}, f)
        
        # Create a minimal valid model_performance.json
        model_perf_json = results_dir / "model_performance.json"
        with open(model_perf_json, 'w') as f:
            json.dump({key: [1.0] for key in REQUIRED_MODEL_KEYS}, f)
        
        # Create a minimal valid final_report.md
        report_md = results_dir / "final_report.md"
        with open(report_md, 'w') as f:
            f.write("# Report\n")
            f.write(f"{MANDATORY_LIMITATIONS_TEXT}\n")
        
        # Create empty filtered_features.csv
        filtered_csv = data_processed / "filtered_features.csv"
        with open(filtered_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["material_id"])
            writer.writeheader()
            writer.writerow({"material_id": "1"})
        
        # Create network_manifest.json
        manifest_json = data_processed / "network_manifest.json"
        with open(manifest_json, 'w') as f:
            json.dump({"materials": []}, f)
        
        # Create runtime.log
        runtime_log = results_dir / "runtime.log"
        with open(runtime_log, 'w') as f:
            f.write("Pipeline completed in 2 hours")
        
        # Create power_analysis.log
        power_log = results_dir / "power_analysis.log"
        with open(power_log, 'w') as f:
            f.write("Power analysis completed")
        
        # Create thermal_predictor.pkl (empty but exists)
        predictor_pkl = models_dir / "thermal_predictor.pkl"
        with open(predictor_pkl, 'w') as f:
            f.write("mock pickle content")
        
        # Patch the paths in validate_artifacts module
        import validate_artifacts
        validate_artifacts.PROJECT_ROOT = tmp_path
        validate_artifacts.DATA_PROCESSED = data_processed
        validate_artifacts.RESULTS_DIR = results_dir
        validate_artifacts.MODELS_DIR = models_dir
        
        # Rebuild the ARTIFACTS_TO_VALIDATE dict with new paths
        validate_artifacts.ARTIFACTS_TO_VALIDATE = {
            "metrics_csv": data_processed / "metrics.csv",
            "correlations_json": results_dir / "correlations.json",
            "model_performance_json": results_dir / "model_performance.json",
            "final_report_md": results_dir / "final_report.md",
            "filtered_features_csv": data_processed / "filtered_features.csv",
            "network_manifest_json": data_processed / "network_manifest.json",
            "runtime_log": results_dir / "runtime.log",
            "power_analysis_log": results_dir / "power_analysis.log",
            "thermal_predictor_pkl": models_dir / "thermal_predictor.pkl",
        }
        
        # Run main
        result = validate_artifacts.main()
        assert result == 0  # Should return 0 if all valid
        
        # Verify logs were printed (we can't easily capture them in this test,
        # but the function should complete without error)