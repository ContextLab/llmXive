"""
Unit tests for T024: Aggregate Results.

These tests verify that the aggregation logic correctly combines
the outputs of T020c, T021a, T021b, T021d, and T022.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code/ to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from modeling.aggregate_results import (
    load_json_file,
    save_json_file,
    aggregate_metrics,
    main
)


class TestLoadJsonFile:
    def test_load_existing_valid_json(self, tmp_path):
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "test.json"
        with open(file_path, "w") as f:
            json.dump(data, f)

        result = load_json_file(file_path)
        assert result == data

    def test_load_non_existent_file(self, tmp_path):
        file_path = tmp_path / "non_existent.json"
        result = load_json_file(file_path)
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        with open(file_path, "w") as f:
            f.write("{ invalid json }")

        result = load_json_file(file_path)
        assert result is None


class TestSaveJsonFile:
    def test_save_valid_data(self, tmp_path):
        data = {"key": "value"}
        file_path = tmp_path / "output.json"

        success = save_json_file(file_path, data)
        assert success is True
        assert file_path.exists()

        with open(file_path, "r") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_save_creates_directories(self, tmp_path):
        data = {"key": "value"}
        file_path = tmp_path / "subdir" / "nested" / "output.json"

        success = save_json_file(file_path, data)
        assert success is True
        assert file_path.exists()


class TestAggregateMetrics:
    def test_aggregate_all_fields_present(self):
        feature_importance = {
            "top_metabolites": [{"name": "A", "importance": 0.9}],
            "method": "mean_decrease_impurity",
            "total_features": 100
        }
        correlation_analysis = {
            "significant_correlations": [{"metabolite": "A", "r": 0.8}],
            "threshold_r": 0.4,
            "threshold_p": 0.01,
            "fdr_method": "benjamini_hochberg"
        }
        model_validation = {
            "balanced_accuracy": 0.85,
            "roc_auc": 0.90,
            "permutation_p_value": 0.01,
            "permutation_n": 1000,
            "validation_method": "hold-out"
        }
        sensitivity_analysis = {
            "thresholds": [0.5, 0.6],
            "fpr_values": [0.1, 0.05],
            "fnr_values": [0.2, 0.1],
            "optimal_threshold": 0.55
        }
        vif_scores = {
            "vif_scores": {"A": 1.2, "B": 2.5},
            "high_collinearity_features": [],
            "threshold_vif": 5.0
        }

        result = aggregate_metrics(
            feature_importance,
            correlation_analysis,
            model_validation,
            sensitivity_analysis,
            vif_scores
        )

        assert "metadata" in result
        assert "model_performance" in result
        assert "feature_importance" in result
        assert "correlation_analysis" in result
        assert "sensitivity_analysis" in result
        assert "collinearity" in result
        assert "summary" in result

        # Check specific values
        assert result["model_performance"]["balanced_accuracy"] == 0.85
        assert result["feature_importance"]["top_metabolites"][0]["name"] == "A"
        assert result["summary"]["num_significant_correlations"] == 1
        assert result["summary"]["model_valid"] is True
        assert result["summary"]["permutation_significant"] is True

    def test_aggregate_with_empty_inputs(self):
        # Test with minimal/empty data structures
        feature_importance = {"top_metabolites": [], "method": "default", "total_features": 0}
        correlation_analysis = {"significant_correlations": [], "threshold_r": 0.4, "threshold_p": 0.01, "fdr_method": "default"}
        model_validation = {"balanced_accuracy": None, "roc_auc": None, "permutation_p_value": 1.0, "permutation_n": 1000, "validation_method": "full"}
        sensitivity_analysis = {"thresholds": [], "fpr_values": [], "fnr_values": [], "optimal_threshold": None}
        vif_scores = {"vif_scores": {}, "high_collinearity_features": [], "threshold_vif": 5.0}

        result = aggregate_metrics(
            feature_importance,
            correlation_analysis,
            model_validation,
            sensitivity_analysis,
            vif_scores
        )

        assert result["model_performance"]["balanced_accuracy"] is None
        assert result["summary"]["model_valid"] is False
        assert result["summary"]["permutation_significant"] is False


class TestMainFunction:
    def test_main_with_all_files_present(self, tmp_path):
        # Create mock input files
        inputs = {
            "feature_importance": {"top_metabolites": [], "method": "test", "total_features": 10},
            "correlation_analysis": {"significant_correlations": [], "threshold_r": 0.4, "threshold_p": 0.01, "fdr_method": "test"},
            "model_validation": {"balanced_accuracy": 0.8, "roc_auc": 0.85, "permutation_p_value": 0.02, "permutation_n": 100, "validation_method": "test"},
            "sensitivity_analysis": {"thresholds": [], "fpr_values": [], "fnr_values": [], "optimal_threshold": None},
            "vif_scores": {"vif_scores": {}, "high_collinearity_features": [], "threshold_vif": 5.0}
        }

        # Mock RESULTS_DIR by temporarily patching the module
        import modeling.aggregate_results as agg_module
        original_results_dir = agg_module.RESULTS_DIR

        # Create a temporary results directory
        temp_results = tmp_path / "results"
        temp_results.mkdir()
        agg_module.RESULTS_DIR = temp_results

        try:
            # Write input files
            for name, data in inputs.items():
                file_map = {
                    "feature_importance": "feature_importance_ranking.json",
                    "correlation_analysis": "correlation_analysis_raw.json",
                    "model_validation": "model_validation.json",
                    "sensitivity_analysis": "sensitivity_analysis.json",
                    "vif_scores": "vif_scores.json"
                }
                with open(temp_results / file_map[name], "w") as f:
                    json.dump(data, f)

            # Capture exit code
            exit_code = None
            try:
                main()
            except SystemExit as e:
                exit_code = e.code

            assert exit_code == 0
            assert (temp_results / "shap_analysis.json").exists()
        finally:
            # Restore original
            agg_module.RESULTS_DIR = original_results_dir

    def test_main_with_missing_file(self, tmp_path, caplog):
        import modeling.aggregate_results as agg_module
        original_results_dir = agg_module.RESULTS_DIR

        temp_results = tmp_path / "results"
        temp_results.mkdir()
        agg_module.RESULTS_DIR = temp_results

        try:
            # Write only one file, leave others missing
            with open(temp_results / "feature_importance_ranking.json", "w") as f:
                json.dump({"top_metabolites": []}, f)

            exit_code = None
            try:
                main()
            except SystemExit as e:
                exit_code = e.code

            assert exit_code == 1
            assert "Missing required input files" in caplog.text
        finally:
            agg_module.RESULTS_DIR = original_results_dir